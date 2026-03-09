import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ArenaStatCard } from "@/components/arena/ArenaStatCard";
import { ControlPanelCard } from "@/components/arena/ControlPanelCard";
import { StatusPill } from "@/components/arena/StatusPill";
import { Button } from "@/components/ui/button";
import { useTournaments, useTournamentTimer, useLeaderboard, useMarketStatus, useRegisterAgent, useStartTestAgent, useTestAgentStatus, useStopTestAgent } from "@/hooks/use-colosseum";
import { Activity, Users, Clock, TrendingUp, Plus, Play, Square, Loader2, Bot } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useToast } from "@/hooks/use-toast";
import { useWallet } from "@/hooks/use-wallet";
import { WalletModal } from "@/components/WalletModal";

const BASE = import.meta.env.VITE_API_BASE_URL || "";

/** Bot avatar: deterministic color from agentId */
function BotAvatar({ agentId, name, size = 36 }: { agentId: string; name?: string; size?: number }) {
  const hash = agentId.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const hue = hash % 360;
  return (
    <div
      className="rounded-full flex items-center justify-center text-white font-bold text-xs shrink-0"
      style={{ width: size, height: size, background: `hsl(${hue}, 60%, 40%)` }}
      title={name || agentId}
    >
      {name ? name.charAt(0).toUpperCase() : <Bot className="h-4 w-4" />}
    </div>
  );
}

const UserPanel = () => {
  const { connected, address } = useWallet();
  const navigate = useNavigate();
  const [walletModalOpen, setWalletModalOpen] = useState(false);
  const { toast } = useToast();
  const { data: tournaments } = useTournaments();
  const activeTournament = tournaments?.[0];
  const { data: timer } = useTournamentTimer(activeTournament?.id);
  const { data: leaderboard } = useLeaderboard(activeTournament?.id);
  const { data: market } = useMarketStatus();
  const registerMut = useRegisterAgent();
  const startTestMut = useStartTestAgent();
  const stopTestMut = useStopTestAgent();

  const [agentId, setAgentId] = useState<string | null>(null);
  const [agentName, setAgentName] = useState<string | null>(null);
  const [testAgentId, setTestAgentId] = useState<string | null>(null);
  const { data: testAgentStatus } = useTestAgentStatus(testAgentId ?? undefined);

  // Trade history state
  const [tradeHistory, setTradeHistory] = useState<any[]>([]);

  // Wallet gate: if not connected, show modal
  useEffect(() => {
    if (!connected) setWalletModalOpen(true);
  }, [connected]);

  // Fetch wallet's registered agent on connect (fixes "My Agents 0" bug)
  useEffect(() => {
    if (!address) return;
    fetch(`${BASE}/agent-api/v1/wallet-agent/${address}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.exists) {
          setAgentId(data.agentId);
          setAgentName(data.name);
        }
      })
      .catch(() => {});
  }, [address]);

  // Fetch trade history when agent + tournament are known
  useEffect(() => {
    if (!activeTournament?.id || !agentId) return;
    fetch(`${BASE}/tournaments/${activeTournament.id}/agents/${agentId}/trades/export?format=json`, {
      headers: { "x-api-key": "dev-gateway-key" },
    })
      .then((r) => r.ok ? r.json() : [])
      .then((data) => setTradeHistory(Array.isArray(data) ? data : []))
      .catch(() => setTradeHistory([]));
  }, [activeTournament?.id, agentId]);

  // Build market chart data from market status (snapshot-based, not time-series)
  const marketChartData = market
    ? Object.entries(market.symbols).map(([sym, s]) => ({
        symbol: sym,
        price: s.effectiveTradingPrice ?? s.aggregatedPrice ?? 0,
      }))
    : [];

  // Find user's agents in leaderboard (now uses real agentId from wallet lookup)
  const myAgents = agentId ? (leaderboard?.filter((a) => a.agentId === agentId) ?? []) : [];

  const handleRegister = () => {
    if (!activeTournament) {
      toast({ title: "No active tournament", description: "Wait for a tournament to be created.", variant: "destructive" });
      return;
    }
    registerMut.mutate(
      { tid: activeTournament.id, agentId, name: agentName },
      {
        onSuccess: () => toast({ title: "Registered!", description: `Agent ${agentName} registered successfully.` }),
        onError: (e) => toast({ title: "Registration failed", description: String(e.message), variant: "destructive" }),
      }
    );
  };

  const fmtTime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold">User Panel</h1>
            <p className="text-sm text-muted-foreground">Register agents and join tournaments</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="neon"
              className="gap-2"
              onClick={() => navigate("/app/onboarding")}
            >
              <Plus className="h-4 w-4" /> Register Agent
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <ArenaStatCard
            title="My Agents"
            value={String(myAgents.length)}
            icon={Users}
            accentColor="cyan"
            subtitle={myAgents.length > 0 ? "registered" : "none yet"}
          />
          <ArenaStatCard
            title="Active Tournaments"
            value={String(tournaments?.length ?? 0)}
            icon={Activity}
            accentColor="gold"
            trend={activeTournament ? "up" : undefined}
            trendValue={activeTournament?.name}
          />
          <ArenaStatCard
            title="Total PnL"
            value={myAgents.length > 0 ? `$${myAgents[0].totalPnl.toFixed(0)}` : "—"}
            icon={TrendingUp}
            accentColor="cyan"
            trend={myAgents.length > 0 && myAgents[0].totalPnl >= 0 ? "up" : "down"}
          />
          <ArenaStatCard
            title="Tournament"
            value={timer ? fmtTime(timer.remainingSec || timer.startsInSec) : "—"}
            icon={Clock}
            accentColor="gold"
            subtitle={timer?.effectiveStatus ?? "no tournament"}
          />
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Market Prices */}
          <ControlPanelCard title="Market Prices — Live" className="md:col-span-2">
            {marketChartData.length > 0 ? (
              <div className="space-y-2">
                {Object.entries(market!.symbols).map(([sym, s]) => {
                  const price = s.effectiveTradingPrice ?? s.aggregatedPrice ?? 0;
                  const confidence = s.aggregatedConfidence ?? "—";
                  return (
                    <div key={sym} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <span className="font-medium">{sym}</span>
                      <div className="text-right">
                        <span className="font-mono text-cyan text-lg">${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                        <span className="ml-2 text-xs text-muted-foreground">{confidence}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Loading market data...</p>
            )}
          </ControlPanelCard>

          {/* Arena Status */}
          <ControlPanelCard title="Arena Status">
            <div className="space-y-4">
              {tournaments && tournaments.length > 0 ? (
                tournaments.map((t) => (
                  <div key={t.id} className="flex items-start justify-between p-3 bg-secondary/50 rounded-lg">
                    <div>
                      <p className="text-sm font-medium">{t.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Balance: ${t.startingBalance} · {t.leverage}x
                      </p>
                    </div>
                    <StatusPill status={t.effectiveStatus as any} />
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No active tournaments</p>
              )}
            </div>
          </ControlPanelCard>
        </div>

        {/* My Agents from leaderboard */}
        <ControlPanelCard title="My Agents">
          {myAgents.length > 0 ? (
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                {myAgents.map((agent) => (
                  <div key={agent.agentId} className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg border border-border">
                    <div className="flex items-center gap-3">
                      <BotAvatar agentId={agent.agentId} name={agent.name} />
                      <div>
                        <p className="font-medium">{agent.name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Rank #{agent.rank} · {agent.trades_count} trades
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-mono ${agent.totalPnl >= 0 ? "text-cyan" : "text-crimson"}`}>
                        {agent.totalPnl >= 0 ? "+" : ""}${agent.totalPnl.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">Equity: ${agent.equity.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
              {/* Test Agent Controls */}
              {testAgentId && testAgentStatus?.running ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 p-3 bg-cyan/10 border border-cyan/30 rounded-lg">
                    <Loader2 className="h-4 w-4 animate-spin text-cyan" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-cyan">Test Agent Running: {testAgentId}</p>
                      <p className="text-xs text-muted-foreground">
                        {testAgentStatus.trades ?? 0} trades executed
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="gap-1"
                      disabled={stopTestMut.isPending}
                      onClick={() => {
                        stopTestMut.mutate(testAgentId, {
                          onSuccess: () => {
                            toast({ title: "Test Agent Stopped" });
                            setTestAgentId(null);
                          },
                        });
                      }}
                    >
                      <Square className="h-3 w-3" /> Stop
                    </Button>
                  </div>
                  {testAgentStatus.log && testAgentStatus.log.length > 0 && (
                    <div className="max-h-32 overflow-y-auto bg-secondary/50 rounded p-2 text-xs font-mono space-y-0.5">
                      {testAgentStatus.log.slice(-8).map((line: string, i: number) => (
                        <div key={i} className="text-muted-foreground">{line}</div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <Button
                  variant="outline"
                  className="gap-2"
                  disabled={startTestMut.isPending}
                  onClick={() => {
                    if (!activeTournament) {
                      toast({ title: "No Tournament", description: "No active tournament found. Please wait for one to be created.", variant: "destructive" });
                      return;
                    }
                    const status = activeTournament.effectiveStatus;
                    if (status === "finished" || status === "archived") {
                      toast({ title: "Tournament Ended", description: "This tournament has already finished. Join a new one.", variant: "destructive" });
                      return;
                    }
                    startTestMut.mutate(activeTournament.id, {
                      onSuccess: (data) => {
                        setTestAgentId(data.agentId);
                        toast({
                          title: "Test Agent Started!",
                          description: `Agent ${data.agentId} is now ${status === "running" ? "trading" : "waiting for tournament to start"}.`,
                        });
                      },
                      onError: (e) => {
                        toast({ title: "Failed to start test agent", description: String(e.message), variant: "destructive" });
                      },
                    });
                  }}
                >
                  {startTestMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Run Test Agent
                </Button>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Register an agent above to see it here. Agent ID must match.
            </p>
          )}
        </ControlPanelCard>
        {/* Trade History Table */}
        <ControlPanelCard title="Trade History">
          {tradeHistory.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground text-xs uppercase tracking-wider">
                    <th className="text-left py-2 px-3 font-medium">Time</th>
                    <th className="text-left py-2 px-3 font-medium">Symbol</th>
                    <th className="text-left py-2 px-3 font-medium">Side</th>
                    <th className="text-right py-2 px-3 font-medium">Qty</th>
                    <th className="text-right py-2 px-3 font-medium">Price</th>
                    <th className="text-right py-2 px-3 font-medium">PnL</th>
                    <th className="text-center py-2 px-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tradeHistory.slice(-50).reverse().map((t, i) => (
                    <tr key={i} className="border-b border-border/30 hover:bg-secondary/30">
                      <td className="py-2 px-3 text-xs text-muted-foreground font-mono">
                        {t.ts ? new Date(t.ts * 1000).toLocaleTimeString() : "—"}
                      </td>
                      <td className="py-2 px-3 font-medium">{t.symbol || "—"}</td>
                      <td className={`py-2 px-3 font-medium ${t.side === "buy" ? "text-cyan" : "text-crimson"}`}>
                        {t.side?.toUpperCase() || "—"}
                      </td>
                      <td className="py-2 px-3 text-right font-mono">{t.qty ?? "—"}</td>
                      <td className="py-2 px-3 text-right font-mono">
                        {t.price ? `$${Number(t.price).toFixed(2)}` : "—"}
                      </td>
                      <td className={`py-2 px-3 text-right font-mono ${(t.pnl ?? 0) >= 0 ? "text-cyan" : "text-crimson"}`}>
                        {t.pnl != null ? `${t.pnl >= 0 ? "+" : ""}$${Number(t.pnl).toFixed(2)}` : "—"}
                      </td>
                      <td className="py-2 px-3 text-center">
                        <span className={`text-xs px-2 py-0.5 rounded ${t.status === "executed" ? "bg-cyan/20 text-cyan" : "bg-crimson/20 text-crimson"}`}>
                          {t.status || "—"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {agentId ? "No trades yet. Start trading to see history here." : "Register an agent to see trade history."}
            </p>
          )}
        </ControlPanelCard>
      </div>

      <WalletModal open={walletModalOpen} onOpenChange={setWalletModalOpen} />
    </AppLayout>
  );
};

export default UserPanel;
