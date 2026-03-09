
from fastapi import APIRouter, Request, HTTPException
from app.types import ConnectAgent, Heartbeat, SubmitSignal
from app import store
from app.services.security import check_api_key, check_timestamp, check_nonce, check_antispam
from app.services.simulator import execute_signal
from app.services.market_data import get_price, resolve_quote, get_effective_trading_price, CHAINLINK_STRICT_ONLY, MARKET_SOURCE, _ensure_ws_manager
from app.services.audit import log_event, log_signal

router = APIRouter(prefix="/gateway", tags=["gateway"])


def _gate(request: Request, agent_id: str, tournament_id: str, timestamp: float, nonce: str):
    check_api_key(request)
    check_timestamp(timestamp)
    check_nonce(agent_id, nonce)
    if tournament_id not in store.tournaments:
        raise HTTPException(404, "Tournament not found")
    if agent_id not in store.agents.get(tournament_id, {}):
        raise HTTPException(404, "Agent not registered in tournament")


@router.post("/connect-agent")
def connect_agent(body: ConnectAgent, request: Request):
    _gate(request, body.agentId, body.tournamentId, body.timestamp, body.nonce)
    agent = store.agents[body.tournamentId][body.agentId]
    agent.connected = True
    log_event(body.tournamentId, body.agentId, "connected")
    return {"status": "connected", "agentId": body.agentId}


@router.post("/heartbeat")
def heartbeat(body: Heartbeat, request: Request):
    _gate(request, body.agentId, body.tournamentId, body.timestamp, body.nonce)
    log_event(body.tournamentId, body.agentId, "heartbeat")
    return {"status": "ok"}


@router.post("/submit-signal")
def submit_signal(body: SubmitSignal, request: Request):
    _gate(request, body.agentId, body.tournamentId, body.timestamp, body.nonce)
    t = store.tournaments[body.tournamentId]
    eff = t.effective_status()
    if eff != "running":
        # Hard gate: no trade execution before running window.
        raise HTTPException(425, f"Tournament not running (effective status: {eff}). Retry when status=running")
    if body.symbol not in t.allowedSymbols:
        log_signal(body.tournamentId, body.agentId, body.symbol, body.side, body.qty,
                   status="rejected", error=f"Symbol not allowed")
        raise HTTPException(400, f"Symbol {body.symbol} not allowed")
    if body.qty <= 0:
        raise HTTPException(400, "qty must be > 0")
    if body.side not in ("buy", "sell"):
        raise HTTPException(400, "side must be buy or sell")

    agent = store.agents[body.tournamentId][body.agentId]

    # === STRICT CHAINLINK ONLY: block if oracle unavailable ===
    if CHAINLINK_STRICT_ONLY and MARKET_SOURCE == "chainlink":
        price, trading_source, stale_reason = get_effective_trading_price(body.symbol)
        if trading_source == "strict_blocked":
            log_signal(body.tournamentId, body.agentId, body.symbol, body.side, body.qty,
                       status="rejected", error=stale_reason)
            raise HTTPException(503, detail=stale_reason)
        exec_source = "chainlink"
    elif MARKET_SOURCE == "ws_mvp":
        # WS MVP: use effective trading price, block if no price
        price, trading_source, stale_reason = get_effective_trading_price(body.symbol)
        if trading_source == "ws_blocked":
            log_signal(body.tournamentId, body.agentId, body.symbol, body.side, body.qty,
                       status="rejected", error=stale_reason)
            raise HTTPException(503, detail=stale_reason)
        exec_source = f"ws_mvp_{trading_source}"
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
        check_antispam(body.tournamentId, body.agentId, notional, agent.starting_balance, t.riskProfile.value)
    except HTTPException as e:
        log_signal(body.tournamentId, body.agentId, body.symbol, body.side, body.qty,
                   price=price, status="rejected", error=str(e.detail))
        raise
    # Resolve leverage: agent-chosen (clamped to tournament max) or tournament default
    effective_leverage = t.leverage
    if body.leverage is not None:
        effective_leverage = max(1.0, min(body.leverage, t.leverage))

    try:
        ev = execute_signal(agent, body.symbol, body.side, body.qty, effective_leverage, price_override=price)
    except ValueError as e:
        log_signal(body.tournamentId, body.agentId, body.symbol, body.side, body.qty,
                   price=price, status="rejected", error=str(e))
        raise HTTPException(400, str(e))
    result = {"status": "executed", "event": ev.model_dump(), "executionSource": exec_source}
    if body.quoteId:
        result["quoteId"] = body.quoteId
    return result
