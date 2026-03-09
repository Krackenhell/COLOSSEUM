import { cn } from "@/lib/utils";
import { RomanBadge } from "./RomanBadge";
import { StatusPill } from "./StatusPill";
import { Bot } from "lucide-react";

interface Agent {
  id: number;
  name: string;
  rank: number;
  pnl: number;
  pnlPercent: number;
  winRate: number;
  trades: number;
  equity: number;
  status: string;
  strategy: string;
  badge: string;
}

interface LeaderboardTableProps {
  agents: Agent[];
  className?: string;
  compact?: boolean;
}

const badgeVariantMap: Record<string, "champion" | "veteran" | "elite" | "warrior" | "recruit"> = {
  Champion: "champion",
  Veteran: "veteran",
  Elite: "elite",
  Warrior: "warrior",
  Recruit: "recruit",
};

export function LeaderboardTable({ agents, className, compact }: LeaderboardTableProps) {
  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-muted-foreground text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-4 font-medium">#</th>
            <th className="text-left py-3 px-4 font-medium">Agent</th>
            {!compact && <th className="text-left py-3 px-4 font-medium">Strategy</th>}
            <th className="text-right py-3 px-4 font-medium">PnL</th>
            <th className="text-right py-3 px-4 font-medium">Win Rate</th>
            {!compact && <th className="text-right py-3 px-4 font-medium">Trades</th>}
            {!compact && <th className="text-right py-3 px-4 font-medium">Equity</th>}
            <th className="text-center py-3 px-4 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((agent) => (
            <tr
              key={agent.id}
              className="border-b border-border/50 hover:bg-secondary/50 transition-colors duration-150"
            >
              <td className="py-3 px-4">
                <span className={cn(
                  "font-display font-bold text-base",
                  agent.rank === 1 && "text-accent",
                  agent.rank === 2 && "text-cyan",
                  agent.rank === 3 && "text-primary",
                  agent.rank > 3 && "text-muted-foreground"
                )}>
                  {agent.rank}
                </span>
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                    style={{ background: `hsl(${(agent.name.split("").reduce((a, c) => a + c.charCodeAt(0), 0)) % 360}, 60%, 40%)` }}
                  >
                    {agent.name.charAt(0).toUpperCase()}
                  </div>
                  <span className="font-medium text-foreground">{agent.name}</span>
                  <RomanBadge
                    label={agent.badge}
                    variant={badgeVariantMap[agent.badge] || "recruit"}
                  />
                </div>
              </td>
              {!compact && (
                <td className="py-3 px-4 text-muted-foreground">{agent.strategy}</td>
              )}
              <td className={cn(
                "py-3 px-4 text-right font-mono font-medium",
                agent.pnl >= 0 ? "text-cyan" : "text-crimson"
              )}>
                {agent.pnl >= 0 ? "+" : ""}{agent.pnl.toLocaleString("en-US", { style: "currency", currency: "USD" })}
                <span className="text-xs ml-1 opacity-70">
                  ({agent.pnlPercent >= 0 ? "+" : ""}{agent.pnlPercent}%)
                </span>
              </td>
              <td className="py-3 px-4 text-right font-mono">{agent.winRate}%</td>
              {!compact && (
                <td className="py-3 px-4 text-right font-mono text-muted-foreground">{agent.trades}</td>
              )}
              {!compact && (
                <td className="py-3 px-4 text-right font-mono">
                  ${agent.equity.toLocaleString()}
                </td>
              )}
              <td className="py-3 px-4 text-center">
                <StatusPill status={agent.status as any} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
