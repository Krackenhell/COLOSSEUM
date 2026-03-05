from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid, time


class TournamentStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    running = "running"
    finished = "finished"


class RiskProfile(str, Enum):
    normal = "normal"
    hft = "hft"


class CreateTournament(BaseModel):
    name: str
    allowedSymbols: list[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    startingBalance: float = 100000.0
    startAt: Optional[float] = None   # unix ts; default = now+60s
    endAt: Optional[float] = None     # unix ts; default = startAt+24h
    riskProfile: RiskProfile = RiskProfile.normal
    leverage: float = 10.0


class Tournament(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    status: TournamentStatus = TournamentStatus.scheduled
    allowedSymbols: list[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    startingBalance: float = 100000.0
    createdAt: float = Field(default_factory=time.time)
    startAt: float = 0.0
    endAt: float = 0.0
    riskProfile: RiskProfile = RiskProfile.normal
    leverage: float = 10.0

    def effective_status(self) -> str:
        now = time.time()
        if self.status == TournamentStatus.finished:
            return "finished"
        if now < self.startAt:
            return "scheduled"
        if now >= self.endAt:
            return "finished"
        return "running"


class RegisterAgent(BaseModel):
    agentId: str
    name: str = ""


# --- Futures position per symbol ---
class FuturesPosition(BaseModel):
    symbol: str = ""
    side: str = "flat"       # long / short / flat
    size: float = 0.0
    entry_price: float = 0.0
    leverage: float = 10.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0


class AgentState(BaseModel):
    agentId: str
    name: str = ""
    tournamentId: str = ""
    cash_balance: float = 100000.0
    starting_balance: float = 100000.0
    positions: dict[str, FuturesPosition] = {}  # symbol -> FuturesPosition
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
    side: str  # buy | sell
    qty: float
    timestamp: float
    nonce: str


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    tournamentId: str
    agentId: str
    type: str
    detail: dict = {}
    ts: float = Field(default_factory=time.time)
