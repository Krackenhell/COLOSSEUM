import os, time
from fastapi import Request, HTTPException
from app import store

AGENT_GATEWAY_KEY = os.environ.get("AGENT_GATEWAY_KEY", "dev-gateway-key")
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "60"))
TS_DRIFT_MS = int(os.environ.get("TS_DRIFT_MS", "30000"))


def check_api_key(request: Request):
    key = request.headers.get("x-api-key", "")
    if key != AGENT_GATEWAY_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    # rate limit
    now = time.time()
    window = now - 60
    hits = store.rate_limits.get(key, [])
    hits = [t for t in hits if t > window]
    if len(hits) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    hits.append(now)
    store.rate_limits[key] = hits


def check_timestamp(ts: float):
    drift = abs(time.time() - ts) * 1000
    if drift > TS_DRIFT_MS:
        raise HTTPException(status_code=400, detail=f"Timestamp drift too large: {drift:.0f}ms")


def check_nonce(agent_id: str, nonce: str):
    used = store.nonces.setdefault(agent_id, set())
    if nonce in used:
        raise HTTPException(status_code=400, detail="Nonce already used")
    used.add(nonce)
