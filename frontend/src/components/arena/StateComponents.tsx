import { cn } from "@/lib/utils";
import { Loader2, AlertTriangle, Inbox } from "lucide-react";

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center justify-center py-12", className)}>
      <Loader2 className="h-8 w-8 animate-spin text-cyan" />
    </div>
  );
}

export function ErrorState({ message = "Something went wrong", className }: { message?: string; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 gap-3", className)}>
      <AlertTriangle className="h-10 w-10 text-crimson" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

export function EmptyState({ message = "No data available", className }: { message?: string; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 gap-3", className)}>
      <Inbox className="h-10 w-10 text-muted-foreground" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
