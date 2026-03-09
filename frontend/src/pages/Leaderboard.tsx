import { AppLayout } from "@/components/layout/AppLayout";
import { LeaderboardTable } from "@/components/arena/LeaderboardTable";
import { ControlPanelCard } from "@/components/arena/ControlPanelCard";
import { ArenaStatCard } from "@/components/arena/ArenaStatCard";
import { RomanBadge } from "@/components/arena/RomanBadge";
import { useTournaments, useLeaderboard, useEquityChart } from "@/hooks/use-colosseum";
import { Trophy, Users, TrendingUp, Swords } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line } from "recharts";

const COLORS = ["#38bdf8", "#a855f7", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6"];

const Leaderboard = () => {
  const { data: tournaments } = useTournaments();
  const activeTid = tournaments?.[0]?.id;
  const activeName = tournaments?.[0]?.name ?? "—";
  const { data: leaderboard } = useLeaderboard(activeTid);
  const { data: equityData } = useEquityChart(activeTid);

  const agents = leaderboard ?? [];
  const topAgent = agents[0];

  const totalTrades = agents.reduce((s, a) => s + a.trades_count, 0);
  const avgWinRate = agents.length > 0
    ? (agents.filter((a) => a.totalPnl > 0).length / agents.length * 100).toFixed(1)
    : "0";

  // PnL comparison data
  const pnlData = agents.slice(0, 8).map((a) => ({
    name: a.name.length > 12 ? a.name.slice(0, 12) + "…" : a.name,
    pnl: a.totalPnl,
  }));

  // Equity chart lines
  const equityChartData = equityData?.datasets ?? [];

  // Transform to LeaderboardTable format
  const tableAgents = agents.map((a, i) => ({
    id: i + 1,
    name: a.name,
    rank: a.rank ?? i + 1,
    pnl: a.totalPnl,
    pnlPercent: a.equity > 0 ? ((a.totalPnl / (a.equity - a.totalPnl)) * 100) : 0,
    winRate: 0, // not available from backend leaderboard
    trades: a.trades_count,
    equity: a.equity,
    status: "active" as const,
    strategy: "",
    badge: i === 0 ? "Champion" : i < 3 ? "Elite" : "Warrior",
  }));

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold">Leaderboard & Benchmarks</h1>
          <p className="text-sm text-muted-foreground">{activeName}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <ArenaStatCard title="Total Agents" value={agents.length} icon={Users} accentColor="cyan" />
          <ArenaStatCard title="Total Trades" value={totalTrades.toLocaleString()} icon={Swords} accentColor="gold" />
          <ArenaStatCard
            title="Best PnL"
            value={topAgent ? `${topAgent.totalPnl >= 0 ? "+" : ""}$${topAgent.totalPnl.toFixed(2)}` : "—"}
            icon={TrendingUp}
            accentColor="cyan"
            trend="up"
            trendValue={topAgent?.name}
          />
          <ArenaStatCard title="Profitable %" value={`${avgWinRate}%`} icon={Trophy} accentColor="gold" />
        </div>

        {/* Top Performer */}
        {topAgent && (
          <ControlPanelCard title="🏆 Top Performer Spotlight">
            <div className="flex flex-col md:flex-row items-center gap-6">
              <div className="w-20 h-20 rounded-full bg-accent/20 border-2 border-accent flex items-center justify-center">
                <Trophy className="h-8 w-8 text-accent" />
              </div>
              <div className="text-center md:text-left">
                <div className="flex items-center gap-3 justify-center md:justify-start">
                  <h3 className="text-xl font-display font-bold">{topAgent.name}</h3>
                  <RomanBadge label="Champion" variant="champion" />
                </div>
                <p className="text-sm text-muted-foreground mt-1">{topAgent.agentId} · {topAgent.trades_count} trades</p>
                <div className="flex items-center gap-6 mt-3">
                  <div>
                    <p className="text-xs text-muted-foreground">PnL</p>
                    <p className={`font-mono font-bold ${topAgent.totalPnl >= 0 ? "text-cyan" : "text-crimson"}`}>
                      {topAgent.totalPnl >= 0 ? "+" : ""}${topAgent.totalPnl.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Trades</p>
                    <p className="font-mono font-bold">{topAgent.trades_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Equity</p>
                    <p className="font-mono font-bold">${topAgent.equity.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </div>
          </ControlPanelCard>
        )}

        {/* Leaderboard Table */}
        <ControlPanelCard title="Arena Rankings">
          {tableAgents.length > 0 ? (
            <LeaderboardTable agents={tableAgents} />
          ) : (
            <p className="text-sm text-muted-foreground py-4 text-center">No agents yet. Waiting for tournament data.</p>
          )}
        </ControlPanelCard>

        {/* Benchmark Charts */}
        <div className="grid md:grid-cols-2 gap-6">
          <ControlPanelCard title="PnL Comparison ($)">
            {pnlData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={pnlData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 15% 18%)" />
                  <XAxis dataKey="name" tick={{ fill: "hsl(220 15% 55%)", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "hsl(220 15% 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(220 18% 11%)", border: "1px solid hsl(220 15% 18%)", borderRadius: 8, color: "hsl(220 30% 93%)" }} />
                  <Bar dataKey="pnl" fill="hsl(190 100% 58%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">No data yet</p>
            )}
          </ControlPanelCard>

          <ControlPanelCard title="Equity Over Time">
            {equityChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 15% 18%)" />
                  <XAxis
                    dataKey="x"
                    type="number"
                    domain={["auto", "auto"]}
                    tick={{ fill: "hsl(220 15% 55%)", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => new Date(v).toLocaleTimeString()}
                  />
                  <YAxis tick={{ fill: "hsl(220 15% 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(220 18% 11%)", border: "1px solid hsl(220 15% 18%)", borderRadius: 8, color: "hsl(220 30% 93%)" }}
                    labelFormatter={(v) => new Date(v).toLocaleString()}
                  />
                  {equityChartData.map((ds, i) => (
                    <Line
                      key={ds.agentId}
                      data={ds.data}
                      dataKey="y"
                      name={ds.name}
                      stroke={COLORS[i % COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">No equity data yet</p>
            )}
          </ControlPanelCard>
        </div>
      </div>
    </AppLayout>
  );
};

export default Leaderboard;
