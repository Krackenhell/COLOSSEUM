import time
import csv
import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.types import CreateTournament, Tournament, RegisterAgent, AgentState, SetStatus, TournamentStatus
from app import store
from app.services.scoring import get_leaderboard
from app.services.audit import log_event, snapshot_equity
from app.services.market_data import get_price

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def _archive_active_tournaments():
    """Archive ALL current active tournaments. Data preserved in archived_tournaments."""
    to_archive = list(store.tournaments.keys())
    for tid in to_archive:
        t = store.tournaments[tid]
        t.status = TournamentStatus.archived
        store.archived_tournaments[tid] = t
        log_event(tid, "system", "auto_archived", {"reason": "new tournament created"})
        del store.tournaments[tid]


@router.post("")
def create_tournament(body: CreateTournament):
    # MVP STRICT: only ONE active tournament at a time (running or scheduled)
    active = [t for t in store.tournaments.values() if t.effective_status() in ("running", "scheduled", "pending")]
    if active:
        names = ", ".join(f"'{t.name}' ({t.effective_status()})" for t in active)
        raise HTTPException(
            409,
            f"Cannot create tournament: already have active tournament(s): {names}. "
            "Finish or archive existing tournament first."
        )

    # Auto-archive all previous non-active tournaments (cleanup)
    _archive_active_tournaments()

    now = time.time()
    start = body.startAt if body.startAt else now + 60
    end = body.endAt if body.endAt else start + 86400
    t = Tournament(name=body.name, allowedSymbols=body.allowedSymbols,
                   startingBalance=body.startingBalance,
                   startAt=start, endAt=end,
                   riskProfile=body.riskProfile, leverage=body.leverage)
    store.tournaments[t.id] = t
    store.agents[t.id] = {}
    store.events[t.id] = []
    # Clear user->tournament mappings (new tournament = fresh registration)
    store.user_agent_tournament.clear()
    return t.model_dump()


@router.get("")
def list_tournaments():
    out = []
    for t in store.tournaments.values():
        d = t.model_dump()
        d["effectiveStatus"] = t.effective_status()
        out.append(d)
    return out


@router.get("/all-history")
def list_all_tournaments():
    """List all tournaments including archived ones (for replay/history)."""
    out = []
    for t in list(store.tournaments.values()) + list(store.archived_tournaments.values()):
        d = t.model_dump()
        d["effectiveStatus"] = t.effective_status()
        # Attach results snapshot for finished/archived tournaments
        eff = t.effective_status()
        if eff in ("finished", "archived"):
            lb = get_leaderboard(t.id)
            top3 = []
            for entry in lb[:3]:
                top3.append({
                    "rank": entry.get("rank", 0),
                    "agentId": entry.get("agentId", ""),
                    "name": entry.get("name", ""),
                    "totalPnl": entry.get("totalPnl", 0),
                    "equity": entry.get("equity", 0),
                    "reward": 0,
                })
            agents_dict = store.agents.get(t.id, {})
            total_trades = sum(a.trades_count for a in agents_dict.values())
            d["results"] = {
                "winner": top3[0]["name"] if top3 else "—",
                "agentCount": len(agents_dict),
                "totalTrades": total_trades,
                "endedAt": t.endAt,
                "top3": top3,
            }
        out.append(d)
    out.sort(key=lambda x: -x["createdAt"])
    return out


@router.post("/{tid}/register-agent")
def register_agent(tid: str, body: RegisterAgent):
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")

    # Rule: registration only BEFORE tournament starts
    eff = t.effective_status()
    if eff not in ("scheduled", "pending"):
        raise HTTPException(400, f"Registration closed: tournament is '{eff}'. Agents can only register before start.")

    # Rule: only ONE agent per user (agentId) across active tournaments
    existing_tid = store.user_agent_tournament.get(body.agentId)
    if existing_tid and existing_tid != tid:
        raise HTTPException(409, f"Agent '{body.agentId}' already registered in tournament '{existing_tid}'. Only one agent per user.")
    if body.agentId in store.agents.get(tid, {}):
        raise HTTPException(409, "Agent already registered in this tournament")

    state = AgentState(agentId=body.agentId, name=body.name or body.agentId,
                       tournamentId=tid, cash_balance=t.startingBalance,
                       starting_balance=t.startingBalance, equity=t.startingBalance)
    store.agents[tid][body.agentId] = state
    store.user_agent_tournament[body.agentId] = tid
    log_event(tid, body.agentId, "registered")
    snapshot_equity(tid, body.agentId, state.equity, state.cash_balance, 0)
    return state.model_dump()


@router.get("/{tid}/agents")
def list_agents(tid: str):
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    return [a.model_dump() for a in store.agents.get(tid, {}).values()]


@router.post("/{tid}/status")
def set_status(tid: str, body: SetStatus):
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    # MVP STRICT: prevent starting if another tournament is already running
    if body.status == TournamentStatus.running:
        running = [ot for ot_id, ot in store.tournaments.items()
                   if ot_id != tid and ot.effective_status() == "running"]
        if running:
            names = ", ".join(f"'{ot.name}'" for ot in running)
            raise HTTPException(409, f"Cannot start: tournament(s) already running: {names}. Stop them first.")

    t.status = body.status
    # Force start: move startAt to now so timer/countdown works correctly
    if body.status == TournamentStatus.running and time.time() < t.startAt:
        t.startAt = time.time()
    log_event(tid, "system", "status_change", {"status": body.status})
    # If finished, auto-archive
    if body.status in (TournamentStatus.finished, TournamentStatus.archived):
        store.archived_tournaments[tid] = t
        if tid in store.tournaments:
            del store.tournaments[tid]
    d = t.model_dump()
    d["effectiveStatus"] = t.effective_status()
    return d


@router.get("/{tid}/timer")
def get_timer(tid: str):
    t = store.tournaments.get(tid) or store.archived_tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    now = time.time()
    eff = t.effective_status()
    remaining = max(0, t.endAt - now) if eff == "running" else 0
    starts_in = max(0, t.startAt - now) if eff == "scheduled" else 0
    return {"tournamentId": tid, "effectiveStatus": eff, "startAt": t.startAt,
            "endAt": t.endAt, "now": now,
            "startsInSec": round(starts_in, 1), "remainingSec": round(remaining, 1)}


@router.get("/{tid}/leaderboard")
def leaderboard(tid: str):
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    return get_leaderboard(tid)


@router.get("/{tid}/events")
def events(tid: str):
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    return [e.model_dump() for e in store.events.get(tid, [])]


@router.get("/{tid}/replay")
def replay_timeline(tid: str):
    """Replay: full timeline of all agent actions/trades for a tournament."""
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    t = store.tournaments.get(tid) or store.archived_tournaments.get(tid)

    # Combine events + signal records into unified timeline
    timeline = []

    # Events
    for ev in store.events.get(tid, []):
        timeline.append({
            "ts": ev.ts, "type": "event", "subtype": ev.type,
            "agentId": ev.agentId, "detail": ev.detail, "id": ev.id
        })

    # Signal history per agent
    for agent_id in store.agents.get(tid, {}):
        key = f"{tid}:{agent_id}"
        for sig in store.signal_history.get(key, []):
            timeline.append({
                "ts": sig.ts, "type": "signal", "subtype": sig.status,
                "agentId": agent_id,
                "detail": {"symbol": sig.symbol, "side": sig.side, "qty": sig.qty,
                           "price": sig.price, "error": sig.error,
                           "equity_after": sig.equity_after}
            })

    timeline.sort(key=lambda x: x["ts"])
    return {
        "tournamentId": tid, "name": t.name, "status": t.effective_status(),
        "startAt": t.startAt, "endAt": t.endAt,
        "totalEvents": len(timeline),
        "timeline": timeline
    }


@router.get("/{tid}/debug/{agent_id}")
def debug_agent(tid: str, agent_id: str):
    """Debug view: why did this agent lose? First-pass diagnostics."""
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    t = store.tournaments.get(tid) or store.archived_tournaments.get(tid)
    agents_dict = store.agents.get(tid, {})
    agent = agents_dict.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found in this tournament")

    key = f"{tid}:{agent_id}"
    signals = store.signal_history.get(key, [])
    equity_snaps = store.equity_snapshots.get(key, [])

    # Diagnostics
    total_trades = agent.trades_count
    rejected = [s for s in signals if s.status == "rejected"]
    executed = [s for s in signals if s.status == "executed"]

    # PnL analysis
    final_pnl = round(agent.equity - agent.starting_balance, 2)
    max_equity = max((s["equity"] for s in equity_snaps), default=agent.starting_balance)
    min_equity = min((s["equity"] for s in equity_snaps), default=agent.starting_balance)
    max_drawdown = round(max_equity - min_equity, 2)
    drawdown_pct = round((max_drawdown / max_equity * 100) if max_equity > 0 else 0, 2)

    # Find worst trade sequences
    losing_trades = []
    for s in signals:
        if s.status == "executed" and s.equity_after > 0:
            losing_trades.append(s)

    # Build equity curve for analysis
    equity_changes = []
    for i in range(1, len(equity_snaps)):
        delta = equity_snaps[i]["equity"] - equity_snaps[i-1]["equity"]
        equity_changes.append({"ts": equity_snaps[i]["ts"], "delta": round(delta, 2)})

    worst_drops = sorted(equity_changes, key=lambda x: x["delta"])[:5]

    # Rank among peers
    all_agents = list(agents_dict.values())
    all_agents.sort(key=lambda a: a.equity, reverse=True)
    rank = next((i+1 for i, a in enumerate(all_agents) if a.agentId == agent_id), len(all_agents))

    # Rejection analysis
    rejection_reasons = {}
    for r in rejected:
        reason = r.error or "unknown"
        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    diagnostics = []
    if final_pnl < 0:
        diagnostics.append(f"Agent finished with negative PnL: {final_pnl}")
    if drawdown_pct > 20:
        diagnostics.append(f"High max drawdown: {drawdown_pct}% (${max_drawdown})")
    if len(rejected) > len(executed) * 0.3:
        diagnostics.append(f"High rejection rate: {len(rejected)}/{len(signals)} signals rejected")
    if total_trades < 3:
        diagnostics.append("Very few trades executed — agent may have been inactive or stuck")
    if not diagnostics:
        diagnostics.append("No obvious issues detected — agent performed within normal parameters")

    return {
        "tournamentId": tid, "agentId": agent_id, "name": agent.name,
        "rank": rank, "totalAgents": len(all_agents),
        "finalEquity": agent.equity, "startingBalance": agent.starting_balance,
        "finalPnl": final_pnl, "realizedPnl": round(agent.realized_pnl, 2),
        "unrealizedPnl": round(agent.unrealized_pnl, 2),
        "maxEquity": round(max_equity, 2), "minEquity": round(min_equity, 2),
        "maxDrawdown": max_drawdown, "maxDrawdownPct": drawdown_pct,
        "totalTrades": total_trades, "totalSignals": len(signals),
        "executedSignals": len(executed), "rejectedSignals": len(rejected),
        "rejectionReasons": rejection_reasons,
        "worstEquityDrops": worst_drops,
        "diagnostics": diagnostics,
        "openPositions": {
            sym: {"side": p.side, "size": round(p.size, 6), "entry": round(p.entry_price, 4)}
            for sym, p in agent.positions.items() if p.side != "flat"
        },
        "equitySnapshots": equity_snaps[-50:],
        "recentSignals": [s.model_dump() for s in signals[-20:]],
    }


@router.get("/{tid}/agents/{agent_id}/trades/export")
def export_agent_trades(tid: str, agent_id: str, format: str = Query("json", pattern="^(json|csv)$")):
    """Export agent trade history in JSON or CSV format."""
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    t = store.tournaments.get(tid) or store.archived_tournaments.get(tid)
    agents_dict = store.agents.get(tid, {})
    if agent_id not in agents_dict:
        raise HTTPException(404, "Agent not found in this tournament")

    key = f"{tid}:{agent_id}"
    signals = store.signal_history.get(key, [])

    rows = []
    for s in signals:
        rows.append({
            "timestamp": s.ts,
            "symbol": s.symbol,
            "side": s.side,
            "qty": s.qty,
            "price": s.price,
            "leverage": s.leverage,
            "realized_pnl": s.equity_after - t.startingBalance if s.status == "executed" else 0,
            "status": s.status,
            "error": s.error,
        })

    if format == "csv":
        if not rows:
            output = io.StringIO("timestamp,symbol,side,qty,price,leverage,realized_pnl,status,error\n")
        else:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={agent_id}_trades.csv"}
        )

    return {"tournamentId": tid, "agentId": agent_id, "trades": rows, "count": len(rows)}


@router.get("/{tid}/agents-studio")
def agents_studio(tid: str):
    """Agent Studio: detailed per-agent data with signals and errors."""
    t = store.tournaments.get(tid) or store.archived_tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    result = []
    for a in store.agents.get(tid, {}).values():
        key = f"{tid}:{a.agentId}"
        signals = store.signal_history.get(key, [])
        recent = [s.model_dump() for s in signals[-10:]]
        errors = [s.model_dump() for s in signals if s.status == "rejected"][-5:]
        positions = {}
        for sym, pos in a.positions.items():
            if pos.side != "flat":
                cur_price = get_price(sym)
                if pos.side == "long":
                    upnl = (cur_price - pos.entry_price) * pos.size
                else:
                    upnl = (pos.entry_price - cur_price) * pos.size
                positions[sym] = {"side": pos.side, "size": round(pos.size, 6),
                                  "entry_price": round(pos.entry_price, 4),
                                  "current_price": round(cur_price, 4),
                                  "unrealized_pnl": round(upnl, 2)}
        result.append({
            "agentId": a.agentId, "name": a.name, "connected": a.connected,
            "riskProfile": t.riskProfile.value, "leverage": t.leverage,
            "equity": round(a.equity, 2), "cash_balance": round(a.cash_balance, 2),
            "realized_pnl": round(a.realized_pnl, 2),
            "unrealized_pnl": round(a.unrealized_pnl, 2),
            "trades_count": a.trades_count, "positions": positions,
            "recent_signals": recent, "recent_errors": errors,
            "total_signals": len(signals),
            "rejected_count": len([s for s in signals if s.status == "rejected"]),
        })
    result.sort(key=lambda x: -x["equity"])
    return result


@router.get("/{tid}/equity-chart")
def equity_chart(tid: str):
    """Equity data for Chart.js."""
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    datasets = []
    for a in store.agents.get(tid, {}).values():
        key = f"{tid}:{a.agentId}"
        snaps = store.equity_snapshots.get(key, [])
        datasets.append({
            "agentId": a.agentId, "name": a.name,
            "data": [{"x": s["ts"] * 1000, "y": s["equity"]} for s in snaps],
        })
    return {"datasets": datasets}
