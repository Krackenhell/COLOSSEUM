import { cn } from "@/lib/utils";

interface LogEntry {
  id: number;
  timestamp: string;
  level: string;
  message: string;
}

interface LogConsoleProps {
  logs: LogEntry[];
  className?: string;
}

const levelStyles: Record<string, string> = {
  INFO: "text-cyan",
  WARN: "text-accent",
  ERROR: "text-crimson",
  DEBUG: "text-muted-foreground",
};

export function LogConsole({ logs, className }: LogConsoleProps) {
  return (
    <div className={cn("bg-background rounded-lg border border-border font-mono text-xs overflow-hidden", className)}>
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-card">
        <span className="w-2.5 h-2.5 rounded-full bg-crimson" />
        <span className="w-2.5 h-2.5 rounded-full bg-accent" />
        <span className="w-2.5 h-2.5 rounded-full bg-cyan" />
        <span className="ml-2 text-muted-foreground text-xs">System Logs</span>
      </div>
      <div className="p-4 max-h-72 overflow-y-auto space-y-1">
        {logs.map((log) => (
          <div key={log.id} className="flex gap-3">
            <span className="text-muted-foreground shrink-0">{log.timestamp.split(" ")[1]}</span>
            <span className={cn("shrink-0 w-12", levelStyles[log.level] || "text-foreground")}>
              [{log.level}]
            </span>
            <span className="text-foreground/80">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
