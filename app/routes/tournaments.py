from fastapi import APIRouter, HTTPException
from app.types import CreateTournament, Tournament, RegisterAgent, AgentState, SetStatus
from app import store
from app.services.scoring import get_leaderboard
from app.services.audit import log_event

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("")
def create_tournament(body: CreateTournament):
    t = Tournament(name=body.name, allowedSymbols=body.allowedSymbols, startingBalance=body.startingBalance)
    store.tournaments[t.id] = t
    store.agents[t.id] = {}
    store.events[t.id] = []
    return t.model_dump()


@router.get("")
def list_tournaments():
    return [t.model_dump() for t in store.tournaments.values()]


@router.post("/{tid}/register-agent")
def register_agent(tid: str, body: RegisterAgent):
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    if body.agentId in store.agents.get(tid, {}):
        raise HTTPException(409, "Agent already registered")
    state = AgentState(
        agentId=body.agentId, name=body.name or body.agentId,
        tournamentId=tid, cash_balance=t.startingBalance,
    )
    store.agents[tid][body.agentId] = state
    log_event(tid, body.agentId, "registered")
    return state.model_dump()


@router.get("/{tid}/agents")
def list_agents(tid: str):
    if tid not in store.tournaments:
        raise HTTPException(404, "Tournament not found")
    return [a.model_dump() for a in store.agents.get(tid, {}).values()]


@router.post("/{tid}/status")
def set_status(tid: str, body: SetStatus):
    t = store.tournaments.get(tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    t.status = body.status
    log_event(tid, "system", "status_change", {"status": body.status})
    return t.model_dump()


@router.get("/{tid}/leaderboard")
def leaderboard(tid: str):
    if tid not in store.tournaments:
        raise HTTPException(404, "Tournament not found")
    return get_leaderboard(tid)


@router.get("/{tid}/events")
def events(tid: str):
    if tid not in store.tournaments:
        raise HTTPException(404, "Tournament not found")
    return [e.model_dump() for e in store.events.get(tid, [])]
