from app.types import AgentState, Event
from app.services.market_data import get_price
from app import store


def execute_signal(agent: AgentState, symbol: str, side: str, qty: float) -> Event:
    price = get_price(symbol)
    cost = price * qty

    if side == "buy":
        if agent.cash_balance < cost:
            raise ValueError(f"Insufficient balance: need {cost:.2f}, have {agent.cash_balance:.2f}")
        agent.cash_balance -= cost
        agent.positions[symbol] = agent.positions.get(symbol, 0.0) + qty
    elif side == "sell":
        held = agent.positions.get(symbol, 0.0)
        if held < qty:
            raise ValueError(f"Insufficient position: need {qty}, have {held}")
        agent.positions[symbol] = held - qty
        agent.cash_balance += cost
        avg_cost = price  # simplified
        agent.realized_pnl += cost - (price * qty)  # simplified; real pnl tracked via balance diff
    else:
        raise ValueError(f"Invalid side: {side}")

    agent.trades_count += 1
    _update_unrealized(agent)

    ev = Event(
        tournamentId=agent.tournamentId,
        agentId=agent.agentId,
        type="trade",
        detail={"symbol": symbol, "side": side, "qty": qty, "price": price, "cost": round(cost, 2)},
    )
    store.events.setdefault(agent.tournamentId, []).append(ev)
    return ev


def _update_unrealized(agent: AgentState):
    u = 0.0
    for sym, qty in agent.positions.items():
        if qty != 0:
            u += qty * get_price(sym)
    agent.unrealized_pnl = round(u, 2)
