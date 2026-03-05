"""Futures-style simulator: market orders only, long/short positions."""
from app.types import AgentState, FuturesPosition, Event
from app.services.market_data import get_price
from app import store


def execute_signal(agent: AgentState, symbol: str, side: str, qty: float, leverage: float = 10.0) -> Event:
    price = get_price(symbol)
    pos = agent.positions.get(symbol, FuturesPosition(symbol=symbol, leverage=leverage))

    notional = price * qty
    margin_required = notional / leverage

    if side == "buy":
        if pos.side == "short":
            # Closing/reducing short
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
                # Open long with remaining
                req_margin = price * remaining / leverage
                if agent.cash_balance < req_margin:
                    raise ValueError(f"Insufficient margin: need {req_margin:.2f}, have {agent.cash_balance:.2f}")
                agent.cash_balance -= req_margin
                pos.side = "long"
                pos.size = remaining
                pos.entry_price = price
                pos.leverage = leverage
        elif pos.side == "long":
            # Adding to long
            req_margin = margin_required
            if agent.cash_balance < req_margin:
                raise ValueError(f"Insufficient margin: need {req_margin:.2f}, have {agent.cash_balance:.2f}")
            new_size = pos.size + qty
            pos.entry_price = (pos.entry_price * pos.size + price * qty) / new_size
            pos.size = new_size
            agent.cash_balance -= req_margin
        else:
            # Flat -> open long
            if agent.cash_balance < margin_required:
                raise ValueError(f"Insufficient margin: need {margin_required:.2f}, have {agent.cash_balance:.2f}")
            agent.cash_balance -= margin_required
            pos.side = "long"
            pos.size = qty
            pos.entry_price = price
            pos.leverage = leverage

    elif side == "sell":
        if pos.side == "long":
            # Closing/reducing long
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
            # Adding to short
            if agent.cash_balance < margin_required:
                raise ValueError(f"Insufficient margin: need {margin_required:.2f}, have {agent.cash_balance:.2f}")
            new_size = pos.size + qty
            pos.entry_price = (pos.entry_price * pos.size + price * qty) / new_size
            pos.size = new_size
            agent.cash_balance -= margin_required
        else:
            # Flat -> open short
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

    ev = Event(
        tournamentId=agent.tournamentId,
        agentId=agent.agentId,
        type="trade",
        detail={
            "symbol": symbol, "side": side, "qty": qty,
            "price": price, "notional": round(notional, 2),
            "pos_side": pos.side, "pos_size": round(pos.size, 6),
        },
    )
    store.events.setdefault(agent.tournamentId, []).append(ev)
    return ev


def update_equity(agent: AgentState, prices: dict[str, float] | None = None):
    """Recalculate unrealized PnL and equity from current prices."""
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
