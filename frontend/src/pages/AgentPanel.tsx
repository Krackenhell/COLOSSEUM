import { useState, useMemo } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { ArenaStatCard } from "@/components/arena/ArenaStatCard";
import { ControlPanelCard } from "@/components/arena/ControlPanelCard";
import { StatusPill } from "@/components/arena/StatusPill";
import { useTournaments, useAgentsStudio, useEquityChart, useEvents } from "@/hooks/use-colosseum";
import { exportAgentTrades } from "@/lib/api";
import { EquityCurveComparison } from "@/components/arena/EquityCurveComparison";
import { DollarSign, TrendingUp, BarChart3, Activity, Settings, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const AgentPanel = () => {
  const { data: tournaments } = useTournaments();
  const activeTid = tournaments?.[0]?.id;
  const { data: agents } = useAgentsStudio(activeTid);
  const { data: equityData } = useEquityChart(activeTid);
  const { data: events } = useEvents(activeTid);

  const [selectedAgent, setSelectedAgent] = useState<string>("");
  const agent = agents?.find((a) => a.agentId === selectedAgent) ?? agents?.[0];

  // Filtered equity data for selected agent
  const filteredEquityData = useMemo(() => {
    if (!equityData) return undefined;
    if (!selectedAgent) return equityData;
    return {
      datasets: equityData.datasets.filter(
        (ds) => ds.agentId === (agent?.agentId ?? "")
      ),
    };
  }, [equityData, selectedAgent, agent?.agentId]);

  // Agent events
  const agentEvents = (events ?? [])
    .filter((e) => !agent || e.agentId === agent.agentId)
    .slice(-10)
    .reverse();

  if (!agent) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">No agents found. Register an agent first.</p>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold">Agent Control Room</h1>
            <p className="text-sm text-muted-foreground">{agent.name} — {agent.agentId}</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusPill status={agent.connected ? "active" : "stopped"} />
            {agents && agents.length > 1 && (
              <select
                className="bg-secondary border border-border rounded px-2 py-1 text-sm"
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
              >
                <option value="">All agents</option>
                {agents.map((a) => (
                  <option key={a.agentId} value={a.agentId}>{a.name}</option>
                ))}
              </select>
            )}
            {activeTid && agent && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={() => exportAgentTrades(activeTid, agent.agentId, "csv")}
              >
                <Download className="h-3.5 w-3.5" />
                Export CSV
              </Button>
            )}
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <ArenaStatCard title="Equity" value={`$${agent.equity.toFixed(2)}`} icon={DollarSign} accentColor="cyan" />
          <ArenaStatCard
            title="Realized PnL"
            value={`${agent.realized_pnl >= 0 ? "+" : ""}$${agent.realized_pnl.toFixed(2)}`}
            icon={TrendingUp}
            accentColor="gold"
            trend={agent.realized_pnl >= 0 ? "up" : "down"}
          />
          <ArenaStatCard title="Total Trades" value={String(agent.trades_count)} icon={BarChart3} accentColor="cyan" />
          <ArenaStatCard
            title="Signals"
            value={`${agent.total_signals}`}
            icon={Activity}
            accentColor="gold"
            subtitle={`${agent.rejected_count} rejected`}
          />
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Equity Curve */}
          <ControlPanelCard title="Equity Curve" className="md:col-span-2">
            <EquityCurveComparison
              equityData={filteredEquityData}
              height={280}
              highlightAgentId={agent?.agentId}
            />
          </ControlPanelCard>

          {/* Event Feed */}
          <ControlPanelCard title="Event Feed">
            <div className="space-y-3 max-h-72 overflow-y-auto">
              {agentEvents.length > 0 ? agentEvents.map((event, i) => (
                <div key={i} className="flex gap-3 text-sm">
                  <span className={cn(
                    "w-1.5 h-1.5 rounded-full mt-1.5 shrink-0",
                    event.type === "connected" && "bg-cyan",
                    event.type === "heartbeat" && "bg-muted-foreground",
                    event.type === "registered" && "bg-accent",
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground/90 truncate">{event.type} — {JSON.stringify(event.detail) ?? ""}</p>
                    <p className="text-xs text-muted-foreground">{new Date(event.ts * 1000).toLocaleTimeString()}</p>
                  </div>
                </div>
              )) : (
                <p className="text-sm text-muted-foreground">No events yet</p>
              )}
            </div>
          </ControlPanelCard>
        </div>

        {/* Positions */}
        <ControlPanelCard
          title="Open Positions"
          headerAction={<span className="text-xs text-muted-foreground">{Object.keys(agent.positions).length} active</span>}
        >
          <div className="overflow-x-auto">
            {Object.keys(agent.positions).length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted-foreground text-xs uppercase tracking-wider border-b border-border">
                    <th className="text-left py-2 px-3 font-medium">Symbol</th>
                    <th className="text-left py-2 px-3 font-medium">Side</th>
                    <th className="text-right py-2 px-3 font-medium">Entry</th>
                    <th className="text-right py-2 px-3 font-medium">Current</th>
                    <th className="text-right py-2 px-3 font-medium">Size</th>
                    <th className="text-right py-2 px-3 font-medium">Unrealized PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(agent.positions).map(([sym, p]) => (
                    <tr key={sym} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                      <td className="py-2.5 px-3 font-medium">{sym}</td>
                      <td className="py-2.5 px-3">
                        <span className={cn("text-xs font-semibold px-2 py-0.5 rounded",
                          p.side === "long" ? "bg-cyan/15 text-cyan" : "bg-crimson/15 text-crimson"
                        )}>
                          {p.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">${p.entry_price.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right font-mono">${p.current_price.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">{p.size}</td>
                      <td className={cn("py-2.5 px-3 text-right font-mono font-medium",
                        p.unrealized_pnl >= 0 ? "text-cyan" : "text-crimson"
                      )}>
                        {p.unrealized_pnl >= 0 ? "+" : ""}${p.unrealized_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-muted-foreground py-4 text-center">No open positions</p>
            )}
          </div>
        </ControlPanelCard>

        {/* Recent Signals */}
        <ControlPanelCard title="Recent Signals" headerAction={<span className="text-xs text-muted-foreground">{agent.total_signals} total</span>}>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {agent.recent_signals.length > 0 ? agent.recent_signals.slice().reverse().map((s, i) => (
              <div key={i} className={cn("text-xs font-mono py-1 px-2 rounded", s.status === "executed" ? "text-cyan" : "text-crimson")}>
                {s.status === "executed" ? "✅" : "❌"} {s.side} {s.qty} {s.symbol}
                {s.price ? ` @ $${s.price.toFixed(2)}` : ""}
                {s.error ? ` — ${s.error}` : ""}
              </div>
            )) : (
              <p className="text-sm text-muted-foreground">No signals yet</p>
            )}
          </div>
        </ControlPanelCard>

        {/* Strategy Info */}
        <ControlPanelCard title="Agent Info">
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { label: "Leverage", value: `${(agent as any).leverage ?? 10}x` },
              { label: "Risk Profile", value: agent.riskProfile },
              { label: "Cash Balance", value: `$${agent.cash_balance.toFixed(2)}` },
              { label: "Unrealized PnL", value: `$${agent.unrealized_pnl.toFixed(2)}` },
              { label: "Total Signals", value: String(agent.total_signals) },
              { label: "Rejected", value: String(agent.rejected_count) },
              { label: "Connected", value: agent.connected ? "Yes" : "No" },
            ].map((param, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <span className="text-sm text-muted-foreground">{param.label}</span>
                <span className="text-sm font-mono font-medium">{param.value}</span>
              </div>
            ))}
          </div>
        </ControlPanelCard>
      </div>
    </AppLayout>
  );
};

export default AgentPanel;
