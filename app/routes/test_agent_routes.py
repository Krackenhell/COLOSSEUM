"""Routes for managing the built-in test AI agent from the UI."""
from fastapi import APIRouter, Request
from app.services.test_ai_agent import start_test_agent, get_test_agent_status, stop_test_agent, list_test_agents

router = APIRouter(prefix="/test-agent", tags=["test-agent"])


@router.post("/start")
def start(body: dict, request: Request):
    """Start a test AI agent for a given tournament."""
    tid = body.get("tournamentId", "")
    if not tid:
        return {"error": "tournamentId required"}
    # Build base_url from request
    base_url = str(request.base_url).rstrip("/")
    result = start_test_agent(base_url, tid)
    return result


@router.get("/status/{agent_id}")
def status(agent_id: str):
    """Get status and log of a test AI agent."""
    s = get_test_agent_status(agent_id)
    if not s:
        return {"error": "Agent not found"}
    return s


@router.post("/stop/{agent_id}")
def stop(agent_id: str):
    """Stop a test AI agent."""
    ok = stop_test_agent(agent_id)
    return {"stopped": ok}


@router.get("/list")
def list_all():
    """List all test AI agents."""
    return list_test_agents()
