"""Deterministic leaderboard: single price snapshot, equity-based sort."""
from app import store
from app.services.market_data import get_price
from app.services.simulator import update_equity


def get_leaderboard(tournament_id: str) -> list[dict]:
    agents = store.agents.get(tournament_id, {})
    t = store.tournaments[tournament_id]

    # Single price snapshot for all symbols used
    all_symbols = set()
    for a in agents.values():
        for sym, pos in a.positions.items():
            if pos.size > 0 and pos.side != "flat":
                all_symbols.add(sym)
    prices = {s: get_price(s) for s in all_symbols}

    board = []
    for a in agents.values():
        update_equity(a, prices)
        total_pnl = round(a.equity - a.starting_balance, 2)
        board.append({
            "agentId": a.agentId,
            "name": a.name,
            "cash_balance": round(a.cash_balance, 2),
            "equity": a.equity,
            "realized_pnl": round(a.realized_pnl, 2),
            "unrealized_pnl": a.unrealized_pnl,
            "totalPnl": total_pnl,
            "trades_count": a.trades_count,
            "positions": {
                sym: {"side": p.side, "size": round(p.size, 6), "entry": round(p.entry_price, 4)}
                for sym, p in a.positions.items() if p.side != "flat"
            },
        })
    # Deterministic sort: by totalPnl desc, then agentId asc (no random jumps)
    board.sort(key=lambda x: (-x["totalPnl"], x["agentId"]))
    return board
