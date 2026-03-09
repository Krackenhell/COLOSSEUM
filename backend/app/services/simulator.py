
"""Futures-style simulator with signal logging and equity snapshots."""
from app.types import AgentState, FuturesPosition, Event
from app.services.market_data import get_price
from app.services.audit import log_signal, snapshot_equity
from app import store


def execute_signal(agent: AgentState, symbol: str, side: str, qty: float, leverage: float = 10.0, price_override: float | None = None) -> Event:
    price = price_override if price_override is not None else get_price(symbol)
    pos = agent.positions.get(symbol, FuturesPosition(symbol=symbol, leverage=leverage))
    notional = price * qty
    margin_required = notional / leverage

    if side == "buy":
        if pos.side == "short":
            close_qty = min(qty, pos.size)
            pnl = (pos.entry_price - price) * close_qty
            pos.realized_pnl += pnl
            agent.realized_pnl += pnl
            agent.cash_balance += pnl + (pos.entry_price * close_qty / leverage)
            pos.size -= close_qty
            remaining = qty - close_qty
            if pos.size == 0:
                pos.side = "flat"
                pos.entry_price = 0.0
            if remaining > 0:
                req_margin = price * remaining / leverage
                if agent.cash_balance < req_margin:
                    raise ValueError(f"Insufficient margin: need {req_margin:.2f}, have {agent.cash_balance:.2f}")
                agent.cash_balance -= req_margin
                pos.side = "long"
                pos.size = remaining
                pos.entry_price = price
                pos.leverage = leverage
        elif pos.side == "long":
            req_margin = margin_required
            if agent.cash_balance < req_margin:
                raise ValueError(f"Insufficient margin: need {req_margin:.2f}, have {agent.cash_balance:.2f}")
            new_size = pos.size + qty
            pos.entry_price = (pos.entry_price * pos.size + price * qty) / new_size
            pos.size = new_size
            agent.cash_balance -= req_margin
        else:
            if agent.cash_balance < margin_required:
                raise ValueError(f"Insufficient margin: need {margin_required:.2f}, have {agent.cash_balance:.2f}")
            agent.cash_balance -= margin_required
            pos.side = "long"
            pos.size = qty
            pos.entry_price = price
            pos.leverage = leverage
    elif side == "sell":
        if pos.side == "long":
            close_qty = min(qty, pos.size)
            pnl = (price - pos.entry_price) * close_qty
            pos.realized_pnl += pnl
            agent.realized_pnl += pnl
            agent.cash_balance += pnl + (pos.entry_price * close_qty / leverage)
            pos.size -= close_qty
            remaining = qty - close_qty
            if pos.size == 0:
                pos.side = "flat"
                pos.entry_price = 0.0
            if remaining > 0:
                req_margin = price * remaining / leverage
                if agent.cash_balance < req_margin:
                    raise ValueError(f"Insufficient margin: need {req_margin:.2f}, have {agent.cash_balance:.2f}")
                agent.cash_balance -= req_margin
                pos.side = "short"
                pos.size = remaining
                pos.entry_price = price
                pos.leverage = leverage
        elif pos.side == "short":
            if agent.cash_balance < margin_required:
                raise ValueError(f"Insufficient margin: need {margin_required:.2f}, have {agent.cash_balance:.2f}")
            new_size = pos.size + qty
            pos.entry_price = (pos.entry_price * pos.size + price * qty) / new_size
            pos.size = new_size
            agent.cash_balance -= margin_required
        else:
            if agent.cash_balance < margin_required:
                raise ValueError(f"Insufficient margin: need {margin_required:.2f}, have {agent.cash_balance:.2f}")
            agent.cash_balance -= margin_required
            pos.side = "short"
            pos.size = qty
            pos.entry_price = price
            pos.leverage = leverage

    agent.positions[symbol] = pos
    agent.trades_count += 1
    update_equity(agent)

    # Log signal and snapshot
    log_signal(agent.tournamentId, agent.agentId, symbol, side, qty,
               price=price, leverage=leverage, status="executed", equity_after=agent.equity)
    snapshot_equity(agent.tournamentId, agent.agentId,
                    agent.equity, agent.cash_balance, agent.realized_pnl)

    ev = Event(
        tournamentId=agent.tournamentId, agentId=agent.agentId, type="trade",
        detail={"symbol": symbol, "side": side, "qty": qty, "price": price,
                "notional": round(notional, 2), "leverage": leverage,
                "pos_side": pos.side, "pos_size": round(pos.size, 6)},
    )
    store.events.setdefault(agent.tournamentId, []).append(ev)
    return ev


def update_equity(agent: AgentState, prices: dict[str, float] | None = None):
    u = 0.0
    for sym, pos in agent.positions.items():
        if pos.size == 0 or pos.side == "flat":
            continue
        p = prices[sym] if prices else get_price(sym)
        if pos.side == "long":
            u += (p - pos.entry_price) * pos.size
        elif pos.side == "short":
            u += (pos.entry_price - p) * pos.size
    agent.unrealized_pnl = round(u, 2)
    agent.equity = round(agent.cash_balance + u, 2)
