
import time
from app.types import Event, SignalRecord
from app import store


def log_event(tournament_id: str, agent_id: str, event_type: str, detail: dict = {}) -> Event:
    ev = Event(tournamentId=tournament_id, agentId=agent_id, type=event_type, detail=detail)
    store.events.setdefault(tournament_id, []).append(ev)
    return ev


def log_signal(tid: str, agent_id: str, symbol: str, side: str, qty: float,
               price: float = 0.0, status: str = "executed", error: str = "",
               equity_after: float = 0.0):
    key = f"{tid}:{agent_id}"
    rec = SignalRecord(symbol=symbol, side=side, qty=qty, price=price,
                       status=status, error=error, equity_after=equity_after)
    store.signal_history.setdefault(key, []).append(rec)
    if len(store.signal_history[key]) > 200:
        store.signal_history[key] = store.signal_history[key][-200:]


def snapshot_equity(tid: str, agent_id: str, equity: float, cash: float, pnl: float):
    key = f"{tid}:{agent_id}"
    store.equity_snapshots.setdefault(key, []).append({
        "ts": time.time(), "equity": round(equity, 2),
        "cash": round(cash, 2), "pnl": round(pnl, 2)
    })
    if len(store.equity_snapshots[key]) > 500:
        store.equity_snapshots[key] = store.equity_snapshots[key][-500:]
