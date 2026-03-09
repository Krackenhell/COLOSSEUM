/**
 * Centralized API client for Colosseum backend.
 * All backend calls go through here.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const GATEWAY_KEY = "dev-gateway-key";

function nonce(): string {
  return crypto.randomUUID();
}

function ts(): number {
  return Date.now() / 1000;
}

async function request<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
  opts?: { bearerToken?: string }
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "x-api-key": GATEWAY_KEY,
  };
  if (opts?.bearerToken) {
    headers["Authorization"] = `Bearer ${opts.bearerToken}`;
  }
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    // Network-level failure (server down, CORS blocked, DNS failure)
    throw new ApiError(
      0,
      `Cannot reach backend (${method} ${path}): ${networkErr instanceof Error ? networkErr.message : "network error"}. Is the server running on ${BASE_URL || "localhost"}?`
    );
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail || err.error || JSON.stringify(err));
  }
  // Handle empty responses (204, etc.)
  const text = await res.text();
  if (!text) return {} as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(res.status, `Invalid JSON from server: ${text.slice(0, 200)}`);
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// ─── Health ───
export const getHealth = () => request<{ status: string }>("GET", "/health");

// ─── Market ───
export const getMarketStatus = () => request<MarketStatusResponse>("GET", "/market-status");

// ─── Tournaments (admin/public) ───
export const listTournaments = () => request<TournamentData[]>("GET", "/tournaments");
export const listAllTournaments = () => request<TournamentData[]>("GET", "/tournaments/all-history");
export const createTournament = (body: CreateTournamentBody) =>
  request<TournamentData>("POST", "/tournaments", body);
export const setTournamentStatus = (tid: string, status: string) =>
  request("POST", `/tournaments/${tid}/status`, { status });
export const getTournamentTimer = (tid: string) =>
  request<TimerData>("GET", `/tournaments/${tid}/timer`);
export const getTournamentLeaderboard = (tid: string) =>
  request<LeaderboardEntry[]>("GET", `/tournaments/${tid}/leaderboard`);
export const getTournamentEvents = (tid: string) =>
  request<EventData[]>("GET", `/tournaments/${tid}/events`);
export const getTournamentAgents = (tid: string) =>
  request<AgentStateData[]>("GET", `/tournaments/${tid}/agents`);
export const getAgentsStudio = (tid: string) =>
  request<AgentStudioEntry[]>("GET", `/tournaments/${tid}/agents-studio`);
export const getEquityChart = (tid: string) =>
  request<EquityChartData>("GET", `/tournaments/${tid}/equity-chart`);
export const getReplay = (tid: string) =>
  request<ReplayData>("GET", `/tournaments/${tid}/replay`);
export const getDebugAgent = (tid: string, agentId: string) =>
  request<DebugData>("GET", `/tournaments/${tid}/debug/${agentId}`);

// ─── Registration (user) ───
export const registerAgent = (tid: string, agentId: string, name?: string) =>
  request("POST", `/tournaments/${tid}/register-agent`, { agentId, name });

// ─── Gateway (agent-level) ───
export const connectAgent = (agentId: string, tournamentId: string) =>
  request("POST", "/gateway/connect-agent", {
    agentId, tournamentId, timestamp: ts(), nonce: nonce(),
  });
export const sendHeartbeat = (agentId: string, tournamentId: string) =>
  request("POST", "/gateway/heartbeat", {
    agentId, tournamentId, timestamp: ts(), nonce: nonce(),
  });
export const submitSignal = (
  agentId: string, tournamentId: string,
  symbol: string, side: string, qty: number
) =>
  request("POST", "/gateway/submit-signal", {
    agentId, tournamentId, symbol, side, qty, timestamp: ts(), nonce: nonce(),
  });

// ─── Test Agent (admin) ───
export const startTestAgent = (tournamentId: string) =>
  request<{ agentId: string }>("POST", "/test-agent/start", { tournamentId });
export const stopTestAgent = (agentId: string) =>
  request("POST", `/test-agent/stop/${agentId}`);
export const getTestAgentStatus = (agentId: string) =>
  request<TestAgentStatus>("GET", `/test-agent/status/${agentId}`);
export const listTestAgents = () =>
  request<TestAgentListEntry[]>("GET", "/test-agent/list");

// ─── Agent API v1 (bearer-key authenticated) ───
export const agentApiRegister = (agentId: string, name: string) =>
  request<{ api_key: string; agentId: string }>("POST", "/agent-api/v1/register", { agentId, name });
export const agentApiBalance = (token: string) =>
  request("GET", "/agent-api/v1/my/balance", undefined, { bearerToken: token });
export const agentApiPositions = (token: string) =>
  request("GET", "/agent-api/v1/my/positions", undefined, { bearerToken: token });

export const updateAgent = (tid: string, body: { agentId: string; name?: string; iconUrl?: string }) =>
  request<AgentStateData>("POST", `/agent-api/v1/tournaments/${tid}/update-agent`, body);

// ─── Trade Export ───
export const exportAgentTrades = (tid: string, agentId: string, format: "json" | "csv" = "csv") => {
  const url = `${BASE_URL}/tournaments/${tid}/agents/${agentId}/trades/export?format=${format}`;
  if (format === "csv") {
    // Direct download
    const a = document.createElement("a");
    a.href = url;
    a.download = `${agentId}_trades.csv`;
    a.click();
    return Promise.resolve();
  }
  return request(`GET`, `/tournaments/${tid}/agents/${agentId}/trades/export?format=json`);
};

// ─── Types ───
export interface TournamentData {
  id: string;
  name: string;
  status: string;
  effectiveStatus: string;
  startAt: number;
  endAt: number;
  allowedSymbols: string[];
  startingBalance: number;
  leverage: number;
  riskProfile: string;
  createdAt: number;
}

export interface CreateTournamentBody {
  name: string;
  startAt?: number;
  endAt?: number;
  leverage?: number;
  riskProfile?: string;
  allowedSymbols?: string[];
  startingBalance?: number;
  prizePool?: number;
}

export interface TimerData {
  tournamentId: string;
  effectiveStatus: string;
  startAt: number;
  endAt: number;
  now: number;
  startsInSec: number;
  remainingSec: number;
}

export interface LeaderboardEntry {
  agentId: string;
  name: string;
  equity: number;
  totalPnl: number;
  realizedPnl: number;
  unrealizedPnl: number;
  trades_count: number;
  rank: number;
  positions: Record<string, unknown>;
}

export interface EventData {
  id: string;
  ts: number;
  type: string;
  agentId: string;
  detail: unknown;
}

export interface AgentStateData {
  agentId: string;
  name: string;
  iconUrl?: string;
  connected: boolean;
  equity: number;
  cash_balance: number;
  realized_pnl: number;
  unrealized_pnl: number;
  trades_count: number;
}

export interface AgentStudioEntry {
  agentId: string;
  name: string;
  iconUrl?: string;
  connected: boolean;
  riskProfile: string;
  equity: number;
  cash_balance: number;
  realized_pnl: number;
  unrealized_pnl: number;
  trades_count: number;
  positions: Record<string, {
    side: string; size: number; entry_price: number;
    current_price: number; unrealized_pnl: number;
  }>;
  recent_signals: SignalRecord[];
  recent_errors: SignalRecord[];
  total_signals: number;
  rejected_count: number;
}

export interface SignalRecord {
  symbol: string;
  side: string;
  qty: number;
  price?: number;
  status: string;
  error?: string;
  ts: number;
}

export interface EquityChartData {
  datasets: {
    agentId: string;
    name: string;
    data: { x: number; y: number }[];
  }[];
}

export interface ReplayData {
  tournamentId: string;
  name: string;
  status: string;
  totalEvents: number;
  timeline: { ts: number; type: string; subtype: string; agentId: string; detail: unknown }[];
}

export interface DebugData {
  agentId: string;
  name: string;
  rank: number;
  totalAgents: number;
  finalEquity: number;
  finalPnl: number;
  maxDrawdownPct: number;
  diagnostics: string[];
  rejectionReasons: Record<string, number>;
  [key: string]: unknown;
}

export interface MarketStatusResponse {
  marketSource: string;
  status?: string;
  symbols: Record<string, {
    aggregatedPrice?: number;
    effectiveTradingPrice?: number;
    aggregatedConfidence?: string;
    aggregatedSourcesUsed?: string[];
    tradingSource?: string;
    staleReason?: string;
    [key: string]: unknown;
  }>;
  tradingMaxOracleAgeSec?: number;
  [key: string]: unknown;
}

export interface TestAgentStatus {
  running: boolean;
  log: string[];
  agentId?: string;
}

export interface TestAgentListEntry {
  agentId: string;
  running: boolean;
  tournamentId?: string;
}
