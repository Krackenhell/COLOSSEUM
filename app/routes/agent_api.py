
"""Agent API v1 with rate limiting and signal logging."""
import time
import uuid
from fastapi import APIRouter, Request, HTTPException
from app.types import SignalRequest, JoinRequest, AgentState
from app import store
from app.services.agent_keys import resolve_key, generate_key, revoke_key, list_keys
from app.services.simulator import execute_signal
from app.services.market_data import get_price, get_all_prices, BASE_PRICES, issue_quote, resolve_quote, get_effective_trading_price, CHAINLINK_STRICT_ONLY, MARKET_SOURCE
from app.services.scoring import get_leaderboard
from app.services.audit import log_event, log_signal
from app.services.security import check_antispam, check_agent_rate_limit

router = APIRouter(prefix="/agent-api/v1", tags=["agent-api"])


@router.post("/register")
def agent_register(body: dict, request: Request):
    agent_id = body.get("agentId", "agent-" + uuid.uuid4().hex[:6])
    name = body.get("name", agent_id)
    expires = body.get("expires_in_hours", 24)
    api_key = generate_key(agent_id, name, expires_in_hours=expires)
    return {"api_key": api_key, "agentId": agent_id, "name": name}


@router.get("/tournaments")
def list_tournaments(request: Request):
    info = resolve_key(request)
    check_agent_rate_limit(info.api_key)
    out = []
    for t in store.tournaments.values():
        d = t.model_dump()
        d["effectiveStatus"] = t.effective_status()
        out.append(d)
    return out


@router.post("/tournaments/{tid}/join")
def join_tournament(tid: str, request: Request, body: JoinRequest = None):
    info = resolve_key(request)
    check_agent_rate_limit(info.api_key)
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    agent_id = info.agentId
    name = (body.name if body and body.name else info.name) or agent_id

    eff = t.effective_status()

    if agent_id not in store.agents.get(tid, {}):
        # New registration: only allowed before tournament starts
        if eff not in ("scheduled", "pending"):
            raise HTTPException(400, f"Registration closed: tournament is '{eff}'. Register before start.")
        # Only one agent per user across active tournaments
        existing_tid = store.user_agent_tournament.get(agent_id)
        if existing_tid and existing_tid != tid:
            raise HTTPException(409, f"Agent '{agent_id}' already registered in tournament '{existing_tid}'.")
        state = AgentState(
            agentId=agent_id, name=name, tournamentId=tid,
            cash_balance=t.startingBalance, starting_balance=t.startingBalance,
            equity=t.startingBalance,
        )
        store.agents.setdefault(tid, {})[agent_id] = state
        store.user_agent_tournament[agent_id] = tid
        log_event(tid, agent_id, "registered")
    agent = store.agents[tid][agent_id]
    agent.connected = True
    log_event(tid, agent_id, "connected")
    info.tournamentId = tid
    return {"status": "joined", "agentId": agent_id, "tournamentId": tid,
            "balance": agent.cash_balance, "allowedSymbols": t.allowedSymbols}


@router.get("/tournaments/{tid}/state")
def tournament_state(tid: str, request: Request):
    resolve_key(request)
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    now = time.time()
    eff = t.effective_status()
    remaining = max(0, t.endAt - now) if eff == "running" else 0
    starts_in = max(0, t.startAt - now) if eff == "scheduled" else 0
    return {"tournamentId": tid, "name": t.name, "effectiveStatus": eff,
            "allowedSymbols": t.allowedSymbols, "leverage": t.leverage,
            "startAt": t.startAt, "endAt": t.endAt,
            "startsInSec": round(starts_in, 1), "remainingSec": round(remaining, 1)}


@router.get("/market-data")
def market_data(request: Request):
    resolve_key(request)
    quote = issue_quote()
    return {
        "prices": quote["prices"],
        "symbols": list(BASE_PRICES.keys()),
        "quoteId": quote["quoteId"],
        "quoteTs": quote["quoteTs"],
        "freshness": quote["freshness"],
    }


@router.get("/market-data/{symbol}")
def market_data_symbol(symbol: str, request: Request):
    resolve_key(request)
    price = get_price(symbol)
    return {"symbol": symbol, "price": price}


@router.post("/signal")
def submit_signal(body: SignalRequest, request: Request):
    info = resolve_key(request)
    check_agent_rate_limit(info.api_key)
    agent_id = info.agentId
    tid = body.tournamentId
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    eff = t.effective_status()
    if eff != "running":
        # Hard gate: no trade execution before running window.
        raise HTTPException(425, f"Tournament not running (status: {eff}). Retry when status=running")
    if body.symbol not in t.allowedSymbols:
        log_signal(tid, agent_id, body.symbol, body.side, body.qty,
                   status="rejected", error="Symbol not allowed")
        raise HTTPException(400, f"Symbol {body.symbol} not allowed")
    if body.qty <= 0:
        raise HTTPException(400, "qty must be > 0")
    if body.side not in ("buy", "sell"):
        raise HTTPException(400, "side must be buy or sell")
    if agent_id not in store.agents.get(tid, {}):
        raise HTTPException(404, "Agent not registered. Call /join first")
    agent = store.agents[tid][agent_id]

    # === STRICT CHAINLINK ONLY: block if oracle unavailable ===
    if CHAINLINK_STRICT_ONLY and MARKET_SOURCE == "chainlink":
        price, trading_source, stale_reason = get_effective_trading_price(body.symbol)
        if trading_source == "strict_blocked":
            log_signal(tid, agent_id, body.symbol, body.side, body.qty,
                       status="rejected", error=stale_reason)
            raise HTTPException(503, detail=stale_reason)
        exec_source = "chainlink"
    else:
        # Quote-based execution with hybrid pricing
        quoted_price, exec_source = resolve_quote(body.quoteId, body.symbol)
        if quoted_price is not None:
            price = quoted_price
        else:
            price, trading_source, _stale_reason = get_effective_trading_price(body.symbol)
            exec_source = f"live_{trading_source}"

    notional = price * body.qty
    try:
        check_antispam(tid, agent_id, notional, agent.starting_balance, t.riskProfile.value)
    except HTTPException as e:
        log_signal(tid, agent_id, body.symbol, body.side, body.qty,
                   price=price, status="rejected", error=str(e.detail))
        raise
    try:
        ev = execute_signal(agent, body.symbol, body.side, body.qty, t.leverage, price_override=price)
    except ValueError as e:
        log_signal(tid, agent_id, body.symbol, body.side, body.qty,
                   price=price, status="rejected", error=str(e))
        raise HTTPException(400, str(e))
    result = {"status": "executed", "event": ev.model_dump(), "executionSource": exec_source}
    if body.quoteId:
        result["quoteId"] = body.quoteId
    return result


@router.get("/my/positions")
def my_positions(request: Request):
    info = resolve_key(request)
    agent_id = info.agentId
    result = {}
    for tid, agents in store.agents.items():
        if agent_id in agents:
            a = agents[agent_id]
            positions = {}
            for sym, pos in a.positions.items():
                if pos.side != "flat":
                    positions[sym] = {"side": pos.side, "size": round(pos.size, 6),
                                      "entry_price": round(pos.entry_price, 4),
                                      "unrealized_pnl": pos.unrealized_pnl}
            result[tid] = {"tournamentId": tid, "positions": positions,
                           "cash_balance": round(a.cash_balance, 2), "equity": round(a.equity, 2)}
    return result


@router.get("/my/balance")
def my_balance(request: Request):
    info = resolve_key(request)
    agent_id = info.agentId
    result = {}
    for tid, agents in store.agents.items():
        if agent_id in agents:
            a = agents[agent_id]
            result[tid] = {"tournamentId": tid, "cash_balance": round(a.cash_balance, 2),
                           "equity": round(a.equity, 2), "realized_pnl": round(a.realized_pnl, 2),
                           "unrealized_pnl": round(a.unrealized_pnl, 2), "trades_count": a.trades_count}
    return result


@router.post("/heartbeat")
def heartbeat(request: Request):
    info = resolve_key(request)
    return {"status": "ok", "agentId": info.agentId, "ts": time.time()}


@router.get("/leaderboard/{tid}")
def leaderboard(tid: str, request: Request):
    resolve_key(request)
    if tid not in store.tournaments and tid not in store.archived_tournaments:
        raise HTTPException(404, "Tournament not found")
    return get_leaderboard(tid)


@router.get("/keys")
def get_keys(request: Request):
    resolve_key(request)
    return list_keys()


@router.post("/keys/{key}/revoke")
def revoke(key: str, request: Request):
    resolve_key(request)
    ok = revoke_key(key)
    if not ok:
        raise HTTPException(404, "Key not found")
    return {"revoked": True}


@router.post("/rotate-key")
def rotate_key(request: Request):
    """During tournament: rotate API key for recovery. Does NOT create a new agent."""
    info = resolve_key(request)
    agent_id = info.agentId
    # Revoke old key
    info.is_active = False
    # Generate new key for same agent
    new_key = generate_key(agent_id, info.name, info.tournamentId)
    return {"api_key": new_key, "agentId": agent_id, "message": "Key rotated. Old key revoked."}
