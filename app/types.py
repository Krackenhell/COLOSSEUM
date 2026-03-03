from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid, time


class TournamentStatus(str, Enum):
    pending = "pending"
    running = "running"
    finished = "finished"


class CreateTournament(BaseModel):
    name: str
    allowedSymbols: list[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    startingBalance: float = 100000.0


class Tournament(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    status: TournamentStatus = TournamentStatus.pending
    allowedSymbols: list[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    startingBalance: float = 100000.0
    createdAt: float = Field(default_factory=time.time)


class RegisterAgent(BaseModel):
    agentId: str
    name: str = ""


class AgentState(BaseModel):
    agentId: str
    name: str = ""
    tournamentId: str = ""
    cash_balance: float = 100000.0
    positions: dict[str, float] = {}
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
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
