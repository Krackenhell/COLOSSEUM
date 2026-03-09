/**
 * EquityCurveComparison — polished multi-agent equity curve chart.
 *
 * Features:
 * - Multi-agent lines with distinct colors
 * - Smooth monotone curves
 * - Interactive legend with show/hide per agent
 * - Custom tooltip: time + equity + delta from start
 * - Normalize toggle (start=100) / absolute mode
 * - Highlight selected/top agent (thicker stroke)
 * - Downsampling for performance (LTTB-like)
 * - Safe adapter for inconsistent data shapes
 */

import { useState, useMemo, useCallback } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import type { EquityChartData } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─── Colors ───
const AGENT_COLORS = [
  "#38bdf8", // sky
  "#a855f7", // purple
  "#22c55e", // green
  "#f59e0b", // amber
  "#ef4444", // red
  "#ec4899", // pink
  "#14b8a6", // teal
  "#6366f1", // indigo
  "#f97316", // orange
  "#84cc16", // lime
];

// ─── Types ───
interface Props {
  equityData: EquityChartData | undefined;
  height?: number;
  highlightAgentId?: string;
  className?: string;
}

interface MergedPoint {
  ts: number;
  [agentKey: string]: number | undefined | null;
}

// ─── Downsampling (largest-triangle-three-buckets simplified) ───
function downsample(data: { x: number; y: number }[], maxPoints: number): { x: number; y: number }[] {
  if (data.length <= maxPoints) return data;
  const sampled: { x: number; y: number }[] = [data[0]];
  const bucketSize = (data.length - 2) / (maxPoints - 2);
  for (let i = 1; i < maxPoints - 1; i++) {
    const start = Math.floor((i - 1) * bucketSize) + 1;
    const end = Math.min(Math.floor(i * bucketSize) + 1, data.length - 1);
    // Pick point with max |y - prev.y| in bucket
    let best = start;
    let bestDelta = -1;
    const prevY = sampled[sampled.length - 1].y;
    for (let j = start; j < end; j++) {
      const d = Math.abs(data[j].y - prevY);
      if (d > bestDelta) { bestDelta = d; best = j; }
    }
    sampled.push(data[best]);
  }
  sampled.push(data[data.length - 1]);
  return sampled;
}

// ─── Safe adapter ───
function adaptDatasets(raw: EquityChartData | undefined) {
  if (!raw?.datasets || !Array.isArray(raw.datasets)) return [];
  return raw.datasets
    .filter((ds) => ds && Array.isArray(ds.data) && ds.data.length > 0)
    .map((ds) => ({
      agentId: ds.agentId ?? "unknown",
      name: ds.name ?? ds.agentId ?? "Agent",
      data: ds.data
        .filter((p) => p && typeof p.x === "number" && typeof p.y === "number")
        .sort((a, b) => a.x - b.x),
    }));
}

const MAX_POINTS_PER_AGENT = 300;

export function EquityCurveComparison({ equityData, height = 340, highlightAgentId, className }: Props) {
  const [normalized, setNormalized] = useState(false);
  const [hiddenAgents, setHiddenAgents] = useState<Set<string>>(new Set());

  const datasets = useMemo(() => adaptDatasets(equityData), [equityData]);

  const toggleAgent = useCallback((agentId: string) => {
    setHiddenAgents((prev) => {
      const next = new Set(prev);
      if (next.has(agentId)) next.delete(agentId);
      else next.add(agentId);
      return next;
    });
  }, []);

  // Merge all agents into unified timeline
  const { mergedData, agentMeta } = useMemo(() => {
    if (datasets.length === 0) return { mergedData: [] as MergedPoint[], agentMeta: [] as { agentId: string; name: string; color: string; startY: number }[] };

    const meta = datasets.map((ds, i) => ({
      agentId: ds.agentId,
      name: ds.name,
      color: AGENT_COLORS[i % AGENT_COLORS.length],
      startY: ds.data[0]?.y ?? 0,
    }));

    // Collect all unique timestamps
    const tsSet = new Set<number>();
    const processedData = datasets.map((ds) => downsample(ds.data, MAX_POINTS_PER_AGENT));
    processedData.forEach((pts) => pts.forEach((p) => tsSet.add(p.x)));
    const allTs = Array.from(tsSet).sort((a, b) => a - b);

    // Build merged rows
    const merged: MergedPoint[] = allTs.map((ts) => {
      const row: MergedPoint = { ts };
      processedData.forEach((pts, i) => {
        // Find closest point at or before ts
        let val: number | null = null;
        for (let j = pts.length - 1; j >= 0; j--) {
          if (pts[j].x <= ts) { val = pts[j].y; break; }
        }
        if (val === null && pts.length > 0 && pts[0].x > ts) {
          // ts is before this agent's data — skip
        }
        if (val !== null) {
          const key = `agent_${i}`;
          if (normalized && meta[i].startY !== 0) {
            row[key] = (val / meta[i].startY) * 100;
          } else {
            row[key] = val;
          }
        }
      });
      return row;
    });

    return { mergedData: merged, agentMeta: meta };
  }, [datasets, normalized]);

  if (datasets.length === 0) {
    return (
      <div className={cn("flex items-center justify-center py-12", className)}>
        <p className="text-sm text-muted-foreground">No equity data yet</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Controls */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2">
          {agentMeta.map((m, i) => {
            const hidden = hiddenAgents.has(m.agentId);
            const isHighlighted = highlightAgentId === m.agentId;
            return (
              <button
                key={m.agentId}
                onClick={() => toggleAgent(m.agentId)}
                className={cn(
                  "flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-all border",
                  hidden
                    ? "opacity-40 border-border"
                    : isHighlighted
                      ? "border-accent bg-accent/10"
                      : "border-border bg-secondary/40 hover:bg-secondary/70"
                )}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: hidden ? "hsl(220 15% 30%)" : m.color }}
                />
                <span className="max-w-[100px] truncate">{m.name}</span>
              </button>
            );
          })}
        </div>

        {/* Normalize toggle */}
        <button
          onClick={() => setNormalized((v) => !v)}
          className={cn(
            "text-xs px-3 py-1 rounded border transition-colors",
            normalized
              ? "border-accent bg-accent/15 text-accent"
              : "border-border bg-secondary/40 text-muted-foreground hover:text-foreground"
          )}
        >
          {normalized ? "Normalized (100)" : "Absolute ($)"}
        </button>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={mergedData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 15% 18%)" />
          <XAxis
            dataKey="ts"
            type="number"
            domain={["dataMin", "dataMax"]}
            tick={{ fill: "hsl(220 15% 55%)", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => {
              const d = new Date(v);
              return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
            }}
          />
          <YAxis
            tick={{ fill: "hsl(220 15% 55%)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => normalized ? `${v.toFixed(0)}` : `$${v.toFixed(0)}`}
          />
          <RechartsTooltip
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              const time = new Date(label as number);
              return (
                <div className="bg-[hsl(220_18%_11%)] border border-[hsl(220_15%_18%)] rounded-lg p-3 text-xs shadow-xl">
                  <p className="text-muted-foreground mb-1.5 font-medium">
                    {time.toLocaleDateString()} {time.toLocaleTimeString()}
                  </p>
                  {payload.map((entry: any) => {
                    const idx = parseInt(entry.dataKey?.split("_")[1] ?? "0");
                    const meta = agentMeta[idx];
                    if (!meta) return null;
                    const val = entry.value as number;
                    const delta = normalized
                      ? val - 100
                      : val - meta.startY;
                    return (
                      <div key={entry.dataKey} className="flex items-center justify-between gap-4 py-0.5">
                        <div className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: meta.color }} />
                          <span className="text-foreground/90 max-w-[120px] truncate">{meta.name}</span>
                        </div>
                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-foreground">
                            {normalized ? val.toFixed(1) : `$${val.toFixed(2)}`}
                          </span>
                          <span className={cn(
                            "text-[10px]",
                            delta >= 0 ? "text-[#22c55e]" : "text-[#ef4444]"
                          )}>
                            {delta >= 0 ? "+" : ""}{normalized ? delta.toFixed(1) : `$${delta.toFixed(2)}`}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            }}
          />
          {agentMeta.map((m, i) => {
            if (hiddenAgents.has(m.agentId)) return null;
            const isHighlighted = highlightAgentId === m.agentId;
            return (
              <Line
                key={m.agentId}
                dataKey={`agent_${i}`}
                name={m.name}
                stroke={m.color}
                strokeWidth={isHighlighted ? 3 : 1.5}
                dot={false}
                type="monotone"
                connectNulls
                strokeOpacity={highlightAgentId && !isHighlighted ? 0.35 : 1}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
