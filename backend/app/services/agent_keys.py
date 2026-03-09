
"""Agent API key management with expiry and revocation."""
import uuid
import time
from fastapi import Request, HTTPException
from app.types import AgentKeyInfo
from app import store

DEFAULT_EXPIRY_HOURS = 24


def generate_key(agent_id: str, name: str = "", tournament_id: str = "",
                 expires_in_hours: float = DEFAULT_EXPIRY_HOURS) -> str:
    api_key = "col_" + uuid.uuid4().hex
    expires_at = time.time() + expires_in_hours * 3600 if expires_in_hours > 0 else 0
    info = AgentKeyInfo(
        api_key=api_key, agentId=agent_id, name=name or agent_id,
        tournamentId=tournament_id, expires_at=expires_at,
    )
    store.agent_api_keys[api_key] = info
    return api_key


def resolve_key(request: Request) -> AgentKeyInfo:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        auth = request.headers.get("x-agent-key", "")
        if not auth:
            raise HTTPException(401, "Missing Authorization header (Bearer <key>) or x-agent-key header")
        key = auth
    else:
        key = auth[7:]

    info = store.agent_api_keys.get(key)
    if not info:
        raise HTTPException(401, "Invalid agent API key")
    if not info.is_active:
        raise HTTPException(401, "API key has been revoked")
    if info.expires_at > 0 and time.time() > info.expires_at:
        raise HTTPException(401, "API key expired")
    info.last_used = time.time()
    return info


def revoke_key(api_key: str) -> bool:
    info = store.agent_api_keys.get(api_key)
    if not info:
        return False
    info.is_active = False
    return True


def list_keys() -> list[dict]:
    now = time.time()
    result = []
    for info in store.agent_api_keys.values():
        remaining = max(0, info.expires_at - now) if info.expires_at > 0 else -1
        result.append({
            "api_key": info.api_key[:12] + "...",
            "api_key_full": info.api_key,
            "agentId": info.agentId,
            "name": info.name,
            "is_active": info.is_active,
            "expired": info.expires_at > 0 and now > info.expires_at,
            "remaining_hours": round(remaining / 3600, 1) if remaining >= 0 else None,
            "last_used": info.last_used,
        })
    return result
