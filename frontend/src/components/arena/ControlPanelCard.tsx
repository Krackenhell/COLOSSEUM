import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface ControlPanelCardProps {
  title: string;
  children: ReactNode;
  className?: string;
  headerAction?: ReactNode;
}

export function ControlPanelCard({ title, children, className, headerAction }: ControlPanelCardProps) {
  return (
    <div className={cn("bg-card rounded-lg border border-border overflow-hidden", className)}>
      <div className="flex items-center justify-between px-5 py-3 border-b border-border">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground font-display">
          {title}
        </h3>
        {headerAction}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}
