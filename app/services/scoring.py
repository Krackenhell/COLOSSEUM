from app import store
from app.services.market_data import get_price


def get_leaderboard(tournament_id: str) -> list[dict]:
    agents = store.agents.get(tournament_id, {})
    board = []
    for a in agents.values():
        # recalc unrealized
        unrealized = sum(qty * get_price(sym) for sym, qty in a.positions.items() if qty != 0)
        total_pnl = round(a.cash_balance + unrealized - store.tournaments[tournament_id].startingBalance, 2)
        board.append({
            "agentId": a.agentId,
            "name": a.name,
            "cash_balance": round(a.cash_balance, 2),
            "positions": dict(a.positions),
            "realized_pnl": round(a.realized_pnl, 2),
            "unrealized_pnl": round(unrealized, 2),
            "totalPnl": total_pnl,
            "trades_count": a.trades_count,
        })
    board.sort(key=lambda x: (-x["totalPnl"], -x["cash_balance"]))
    return board
