from app.types import Event
from app import store


def log_event(tournament_id: str, agent_id: str, event_type: str, detail: dict = {}) -> Event:
    ev = Event(tournamentId=tournament_id, agentId=agent_id, type=event_type, detail=detail)
    store.events.setdefault(tournament_id, []).append(ev)
    return ev
