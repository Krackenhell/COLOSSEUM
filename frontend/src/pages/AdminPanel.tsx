import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { ControlPanelCard } from "@/components/arena/ControlPanelCard";
import { ArenaStatCard } from "@/components/arena/ArenaStatCard";
import { StatusPill } from "@/components/arena/StatusPill";
import { LogConsole } from "@/components/arena/LogConsole";
import { Button } from "@/components/ui/button";
import {
  useTournaments, useHealth, useTournamentTimer, useAgentsStudio,
  useEvents, useCreateTournament, useSetTournamentStatus,
  useStartTestAgent, useStopTestAgent, useTestAgents, useTestAgentStatus,
  useMarketStatus,
} from "@/hooks/use-colosseum";
import { Shield, Users, Activity, AlertTriangle, Play, Pause, RotateCcw, Plus, Bot, Square } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const AdminPanel = () => {
  const { toast } = useToast();
  const { data: tournaments } = useTournaments();
  const { data: health } = useHealth();
  const { data: market } = useMarketStatus();
  const { data: testAgents } = useTestAgents();
  const createMut = useCreateTournament();
  const statusMut = useSetTournamentStatus();
  const startTestMut = useStartTestAgent();
  const stopTestMut = useStopTestAgent();

  const [selectedTid, setSelectedTid] = useState<string>("");
  const activeTid = selectedTid || tournaments?.[0]?.id || "";

  const { data: agents } = useAgentsStudio(activeTid || undefined);
  const { data: timer } = useTournamentTimer(activeTid || undefined);
  const { data: events } = useEvents(activeTid || undefined);

  // Track test agent for log polling
  const [testAgentId, setTestAgentId] = useState<string>("");
  const { data: testStatus } = useTestAgentStatus(testAgentId || undefined);

  const [tName, setTName] = useState("Demo Tournament");

  // Default start time: +10 minutes from now, rounded to nearest minute
  const defaultStart = () => {
    const d = new Date(Date.now() + 10 * 60_000);
    d.setSeconds(0, 0);
    return d.toISOString().slice(0, 16); // "YYYY-MM-DDTHH:mm" for datetime-local
  };
  const [tStartStr, setTStartStr] = useState(defaultStart);

  const handleCreate = () => {
    const startEpoch = new Date(tStartStr).getTime() / 1000;
    const now = Date.now() / 1000;
    if (startEpoch <= now + 30) {
      toast({ title: "Invalid start time", description: "Start time must be at least 30 seconds in the future.", variant: "destructive" });
      return;
    }
    createMut.mutate(
      { name: tName, startAt: startEpoch, endAt: startEpoch + 86400, leverage: 10, riskProfile: "normal" },
      {
        onSuccess: (data) => {
          setSelectedTid(data.id);
          toast({ title: "Tournament created", description: data.id });
        },
        onError: (e) => toast({ title: "Error", description: e.message, variant: "destructive" }),
      }
    );
  };

  const handleStatus = (status: string) => {
    if (!activeTid) return;
    statusMut.mutate(
      { tid: activeTid, status },
      {
        onSuccess: () => toast({ title: `Status → ${status}` }),
        onError: (e) => toast({ title: "Error", description: e.message, variant: "destructive" }),
      }
    );
  };

  const handleStartTest = () => {
    if (!activeTid) return;
    startTestMut.mutate(activeTid, {
      onSuccess: (data) => {
        setTestAgentId(data.agentId);
        toast({ title: "Test AI started", description: data.agentId });
      },
      onError: (e) => toast({ title: "Error", description: e.message, variant: "destructive" }),
    });
  };

  const handleStopTest = (id: string) => {
    stopTestMut.mutate(id, {
      onSuccess: () => toast({ title: "Test AI stopped" }),
    });
  };

  // Build log entries from events
  const logEntries = (events ?? []).slice(-30).reverse().map((e, i) => ({
    id: i,
    timestamp: new Date(e.ts * 1000).toLocaleString(),
    level: e.type === "error" ? "ERROR" : e.type === "heartbeat" ? "INFO" : "INFO",
    message: `${e.type} | ${e.agentId} | ${typeof e.detail === "object" ? JSON.stringify(e.detail) : e.detail ?? ""}`,
  }));

  const activeAgents = agents?.filter((a) => a.connected).length ?? 0;
  const totalPositions = agents?.reduce((sum, a) => sum + Object.keys(a.positions).length, 0) ?? 0;
  const warnings = agents?.reduce((sum, a) => sum + a.rejected_count, 0) ?? 0;

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold">Admin Control Center</h1>
            <p className="text-sm text-muted-foreground">
              Backend: {health?.status === "ok" ? "🟢 Online" : "🔴 Offline"}
              {market ? ` · ${market.marketSource}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <input
              className="bg-secondary border border-border rounded px-2 py-1 text-sm w-40"
              value={tName}
              onChange={(e) => setTName(e.target.value)}
              placeholder="Tournament name"
            />
            <input
              type="datetime-local"
              className="bg-secondary border border-border rounded px-2 py-1 text-sm"
              value={tStartStr}
              onChange={(e) => setTStartStr(e.target.value)}
            />
            <Button variant="neon" className="gap-2" onClick={handleCreate} disabled={createMut.isPending}>
              <Plus className="h-4 w-4" /> New Tournament
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <ArenaStatCard title="Active Agents" value={String(activeAgents)} icon={Users} accentColor="cyan" />
          <ArenaStatCard title="Open Positions" value={String(totalPositions)} icon={Activity} accentColor="gold" />
          <ArenaStatCard
            title="System Health"
            value={health?.status === "ok" ? "Online" : "Offline"}
            icon={Shield}
            accentColor="cyan"
            trend={health?.status === "ok" ? "up" : "down"}
            trendValue={timer?.effectiveStatus ?? "—"}
          />
          <ArenaStatCard title="Rejected Signals" value={String(warnings)} icon={AlertTriangle} accentColor="crimson" />
        </div>

        {/* Tournament Manager */}
        <ControlPanelCard title="Tournament Manager">
          <div className="space-y-3">
            {tournaments && tournaments.length > 0 ? (
              tournaments.map((t) => (
                <div
                  key={t.id}
                  className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-colors ${
                    t.id === activeTid ? "bg-secondary/50 border-cyan/50" : "bg-secondary/30 border-border"
                  }`}
                  onClick={() => setSelectedTid(t.id)}
                >
                  <div>
                    <div className="flex items-center gap-3">
                      <p className="font-medium">{t.name}</p>
                      <StatusPill status={t.effectiveStatus as any} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {t.id} · {t.allowedSymbols?.join(", ")} · {t.leverage}x · ${t.startingBalance}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {(t.effectiveStatus === "scheduled" || t.effectiveStatus === "pending") && (
                      <Button variant="neon" size="sm" onClick={(e) => { e.stopPropagation(); handleStatus("running"); }}>
                        <Play className="h-3.5 w-3.5" />
                      </Button>
                    )}
                    {t.effectiveStatus === "running" && (
                      <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleStatus("finished"); }}>
                        <Pause className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No tournaments. Create one above.</p>
            )}
          </div>
        </ControlPanelCard>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Agent Controls */}
          <ControlPanelCard title="Agent Controls">
            <div className="space-y-2">
              {agents && agents.length > 0 ? (
                agents.slice(0, 10).map((agent, i) => (
                  <div key={agent.agentId} className="flex items-center justify-between p-3 bg-secondary/20 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-muted-foreground w-4">#{i + 1}</span>
                      <span className="text-sm font-medium">{agent.name}</span>
                      <StatusPill status={agent.connected ? "active" : "stopped"} />
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-mono">${agent.equity.toFixed(0)}</span>
                      <span className={agent.realized_pnl >= 0 ? "text-cyan" : "text-crimson"}>
                        {agent.realized_pnl >= 0 ? "+" : ""}{agent.realized_pnl.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No agents registered yet.</p>
              )}
            </div>
          </ControlPanelCard>

          {/* Test AI + Diagnostics */}
          <ControlPanelCard title="Test AI Agent">
            <div className="space-y-3">
              <div className="flex gap-2">
                <Button className="gap-2" onClick={handleStartTest} disabled={startTestMut.isPending || !activeTid}>
                  <Bot className="h-4 w-4" /> Start Test AI
                </Button>
              </div>
              {testAgents && testAgents.length > 0 && (
                <div className="space-y-2">
                  {testAgents.map((ta) => (
                    <div key={ta.agentId} className="flex items-center justify-between p-2 bg-secondary/20 rounded">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${ta.running ? "bg-cyan" : "bg-muted-foreground"}`} />
                        <span className="text-xs font-mono">{ta.agentId}</span>
                      </div>
                      {ta.running && (
                        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-crimson" onClick={() => handleStopTest(ta.agentId)}>
                          <Square className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {testStatus?.log && (
                <div className="bg-background/50 border border-border rounded p-2 max-h-40 overflow-y-auto font-mono text-xs">
                  {testStatus.log.slice(-15).map((line, i) => (
                    <div key={i} className="text-muted-foreground">{line}</div>
                  ))}
                </div>
              )}
            </div>
          </ControlPanelCard>
        </div>

        {/* Market Status */}
        {market && (
          <ControlPanelCard title={`Market Status — ${market.marketSource.toUpperCase()}`}>
            <div className="grid md:grid-cols-3 gap-3">
              {Object.entries(market.symbols).map(([sym, s]) => {
                const price = s.effectiveTradingPrice ?? s.aggregatedPrice ?? 0;
                const confidence = s.aggregatedConfidence;
                return (
                  <div key={sym} className="flex items-center justify-between p-3 bg-secondary/20 rounded-lg">
                    <span className="text-sm font-medium">{sym}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-cyan">${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                      {confidence && (
                        <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${
                          confidence === "high" ? "bg-cyan/20 text-cyan" :
                          confidence === "medium" ? "bg-accent/20 text-accent" :
                          "bg-crimson/20 text-crimson"
                        }`}>
                          {confidence}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </ControlPanelCard>
        )}

        {/* Logs */}
        <ControlPanelCard title="Event Log">
          <LogConsole logs={logEntries} />
        </ControlPanelCard>
      </div>
    </AppLayout>
  );
};

export default AdminPanel;
