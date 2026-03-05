from fastapi import APIRouter, Request, HTTPException
from app.types import ConnectAgent, Heartbeat, SubmitSignal
from app import store
from app.services.security import check_api_key, check_timestamp, check_nonce, check_antispam
from app.services.simulator import execute_signal
from app.services.market_data import get_price
from app.services.audit import log_event

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

    # Timer-based: only accept signals when effective status is running
    eff = t.effective_status()
    if eff != "running":
        raise HTTPException(400, f"Tournament not running (effective status: {eff})")

    if body.symbol not in t.allowedSymbols:
        raise HTTPException(400, f"Symbol {body.symbol} not allowed")
    if body.qty <= 0:
        raise HTTPException(400, "qty must be > 0")
    if body.side not in ("buy", "sell"):
        raise HTTPException(400, "side must be buy or sell")

    agent = store.agents[body.tournamentId][body.agentId]

    # Anti-spam check
    price = get_price(body.symbol)
    notional = price * body.qty
    check_antispam(body.tournamentId, body.agentId, notional, agent.starting_balance, t.riskProfile.value)

    try:
        ev = execute_signal(agent, body.symbol, body.side, body.qty, t.leverage)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "executed", "event": ev.model_dump()}
