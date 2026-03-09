
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid, time


class TournamentStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    running = "running"
    finished = "finished"
    archived = "archived"


class RiskProfile(str, Enum):
    normal = "normal"
    hft = "hft"


class CreateTournament(BaseModel):
    name: str
    allowedSymbols: list[str] = ["BTCUSDT", "ETHUSDT", "AVAXUSDT"]
    startingBalance: float = 100000.0
    startAt: Optional[float] = None
    endAt: Optional[float] = None
    riskProfile: RiskProfile = RiskProfile.normal
    leverage: float = 10.0
    prizePool: float = 0.0


class Tournament(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    status: TournamentStatus = TournamentStatus.scheduled
    allowedSymbols: list[str] = ["BTCUSDT", "ETHUSDT", "AVAXUSDT"]
    startingBalance: float = 100000.0
    createdAt: float = Field(default_factory=time.time)
    startAt: float = 0.0
    endAt: float = 0.0
    riskProfile: RiskProfile = RiskProfile.normal
    leverage: float = 10.0
    prizePool: float = 0.0
    results: Optional[dict] = None

    def effective_status(self) -> str:
        now = time.time()
        if self.status == TournamentStatus.finished:
            return "finished"
        if self.status == TournamentStatus.running:
            # Explicitly forced to running — honor it, but check endAt
            if now >= self.endAt:
                return "finished"
            return "running"
        if now < self.startAt:
            return "scheduled"
        if now >= self.endAt:
            return "finished"
        return "running"


class RegisterAgent(BaseModel):
    agentId: str
    name: str = ""
    iconUrl: Optional[str] = None


class FuturesPosition(BaseModel):
    symbol: str = ""
    side: str = "flat"
    size: float = 0.0
    entry_price: float = 0.0
    leverage: float = 10.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0


class AgentState(BaseModel):
    agentId: str
    name: str = ""
    iconUrl: Optional[str] = None
    tournamentId: str = ""
    cash_balance: float = 100000.0
    starting_balance: float = 100000.0
    positions: dict[str, FuturesPosition] = {}
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    equity: float = 100000.0
    trades_count: int = 0
    connected: bool = False


class SetStatus(BaseModel):
    status: TournamentStatus


class ConnectAgent(BaseModel):
    agentId: str
    tournamentId: str
    timestamp: float
    nonce: str


class Heartbeat(BaseModel):
    agentId: str
    tournamentId: str
    timestamp: float
    nonce: str


class SubmitSignal(BaseModel):
    agentId: str
    tournamentId: str
    symbol: str
    side: str
    qty: float
    timestamp: float
    nonce: str
    quoteId: Optional[str] = None
    leverage: Optional[float] = None  # agent-chosen leverage; None = use tournament default


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    tournamentId: str
    agentId: str
    type: str
    detail: dict = {}
    ts: float = Field(default_factory=time.time)


class SignalRecord(BaseModel):
    ts: float = Field(default_factory=time.time)
    symbol: str
    side: str
    qty: float
    price: float = 0.0
    leverage: float = 1.0
    status: str = "executed"
    error: str = ""
    equity_after: float = 0.0


class AgentKeyInfo(BaseModel):
    api_key: str
    agentId: str
    name: str = ""
    tournamentId: str = ""
    created_at: float = Field(default_factory=time.time)
    expires_at: float = 0.0
    is_active: bool = True
    last_used: float = 0.0


class SignalRequest(BaseModel):
    tournamentId: str
    symbol: str
    side: str
    qty: float
    quoteId: Optional[str] = None
    leverage: Optional[float] = None  # agent-chosen leverage; None = use tournament default


class JoinRequest(BaseModel):
    name: str = ""
    iconUrl: Optional[str] = None
