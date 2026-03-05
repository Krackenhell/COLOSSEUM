"""Security: API key, timestamp, nonce, anti-spam rate limiting."""
import os, time
from collections import deque
from fastapi import Request, HTTPException
from app import store

AGENT_GATEWAY_KEY = os.environ.get("AGENT_GATEWAY_KEY", "dev-gateway-key")
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "60"))
TS_DRIFT_MS = int(os.environ.get("TS_DRIFT_MS", "30000"))

# Anti-spam profiles
RISK_PROFILES = {
    "normal": {"max_orders": 12, "window_sec": 10, "max_notional_pct": 50},
    "hft":    {"max_orders": 40, "window_sec": 10, "max_notional_pct": 80},
}


def check_api_key(request: Request):
    key = request.headers.get("x-api-key", "")
    if key != AGENT_GATEWAY_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
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


def check_antispam(tournament_id: str, agent_id: str, notional: float, starting_balance: float, risk_profile: str = "normal"):
    """Check order flood and notional guardrails. No naive side cooldown."""
    profile = RISK_PROFILES.get(risk_profile, RISK_PROFILES["normal"])
    key = f"{tournament_id}:{agent_id}"
    now = time.time()
    window = now - profile["window_sec"]

    dq = store.agent_order_timestamps.get(key)
    if dq is None:
        dq = deque()
        store.agent_order_timestamps[key] = dq

    # Evict old
    while dq and dq[0] < window:
        dq.popleft()

    if len(dq) >= profile["max_orders"]:
        raise HTTPException(
            status_code=429,
            detail=f"ANTISPAM: {len(dq)}/{profile['max_orders']} orders in {profile['window_sec']}s window ({risk_profile} profile)"
        )

    max_notional = starting_balance * profile["max_notional_pct"] / 100
    if notional > max_notional:
        raise HTTPException(
            status_code=400,
            detail=f"ANTISPAM: notional {notional:.2f} exceeds {profile['max_notional_pct']}% of balance ({max_notional:.2f})"
        )

    dq.append(now)
