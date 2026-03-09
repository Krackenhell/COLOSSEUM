import { cn } from "@/lib/utils";

interface StatusPillProps {
  status: "active" | "paused" | "stopped" | "completed" | "upcoming" | "error";
  className?: string;
}

const statusStyles = {
  active: "bg-cyan/15 text-cyan border-cyan/30",
  paused: "bg-accent/15 text-accent border-accent/30",
  stopped: "bg-crimson/15 text-crimson border-crimson/30",
  completed: "bg-muted text-muted-foreground border-border",
  upcoming: "bg-primary/15 text-primary border-primary/30",
  error: "bg-crimson/15 text-crimson border-crimson/30",
};

export function StatusPill({ status, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border",
        statusStyles[status],
        className
      )}
    >
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full",
          status === "active" && "bg-cyan animate-pulse-glow",
          status === "paused" && "bg-accent",
          status === "stopped" && "bg-crimson",
          status === "completed" && "bg-muted-foreground",
          status === "upcoming" && "bg-primary",
          status === "error" && "bg-crimson animate-pulse-glow"
        )}
      />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
