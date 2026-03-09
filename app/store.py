
from app.types import Tournament, AgentState, Event, AgentKeyInfo, SignalRecord
from collections import deque
import time

tournaments: dict[str, Tournament] = {}           # active tournaments only
archived_tournaments: dict[str, Tournament] = {}   # archived (historical) tournaments
agents: dict[str, dict[str, AgentState]] = {}
events: dict[str, list[Event]] = {}
nonces: dict[str, set[str]] = {}
rate_limits: dict[str, list[float]] = {}
agent_order_timestamps: dict[str, deque] = {}
agent_api_keys: dict[str, AgentKeyInfo] = {}

# Agent Studio data
signal_history: dict[str, list[SignalRecord]] = {}   # "tid:agentId" -> signals
equity_snapshots: dict[str, list[dict]] = {}          # "tid:agentId" -> [{ts,equity,cash,pnl}]

# Track which user (agentId from API key) registered in which active tournament
# agentId -> tournamentId  (only one agent per user across active tournaments)
user_agent_tournament: dict[str, str] = {}

# MVP: wallet -> agent info mapping (one agent per wallet)
wallet_agents: dict[str, dict] = {}
