import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface ArenaStatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  className?: string;
  accentColor?: "cyan" | "gold" | "crimson";
}

const accentStyles = {
  cyan: "border-t-cyan",
  gold: "border-t-gold",
  crimson: "border-t-crimson",
};

export function ArenaStatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  className,
  accentColor = "cyan",
}: ArenaStatCardProps) {
  return (
    <div
      className={cn(
        "bg-card rounded-lg border border-border p-5 card-hover border-t-2",
        accentStyles[accentColor],
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </div>
      <div className="text-2xl font-bold text-foreground font-display">{value}</div>
      <div className="flex items-center gap-2 mt-1">
        {trend && trendValue && (
          <span
            className={cn(
              "text-xs font-medium",
              trend === "up" && "text-cyan",
              trend === "down" && "text-crimson",
              trend === "neutral" && "text-muted-foreground"
            )}
          >
            {trend === "up" ? "▲" : trend === "down" ? "▼" : "—"} {trendValue}
          </span>
        )}
        {subtitle && (
          <span className="text-xs text-muted-foreground">{subtitle}</span>
        )}
      </div>
    </div>
  );
}
