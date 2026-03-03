from app.types import Tournament, AgentState, Event

tournaments: dict[str, Tournament] = {}
agents: dict[str, dict[str, AgentState]] = {}   # tournamentId -> agentId -> state
events: dict[str, list[Event]] = {}              # tournamentId -> events
nonces: dict[str, set[str]] = {}                 # agentId -> used nonces
rate_limits: dict[str, list[float]] = {}         # api_key -> list of timestamps
