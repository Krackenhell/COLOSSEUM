from app.types import Tournament, AgentState, Event
from collections import deque
import time

tournaments: dict[str, Tournament] = {}
agents: dict[str, dict[str, AgentState]] = {}   # tournamentId -> agentId -> state
events: dict[str, list[Event]] = {}              # tournamentId -> events
nonces: dict[str, set[str]] = {}                 # agentId -> used nonces
rate_limits: dict[str, list[float]] = {}         # api_key -> list of timestamps

# Anti-spam: per-agent order timestamps within sliding window
agent_order_timestamps: dict[str, deque] = {}    # "tid:agentId" -> deque of timestamps
