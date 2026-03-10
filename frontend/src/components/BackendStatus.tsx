import { useHealth } from "@/hooks/use-colosseum";

export function BackendStatus() {
  const { isError, error, failureCount } = useHealth();

  if (!isError || failureCount < 2) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-destructive/90 text-destructive-foreground text-center py-2 px-4 text-sm backdrop-blur-sm">
      ⚠️ Backend unavailable — retrying automatically...
      <span className="ml-2 opacity-70 text-xs">
        ({error?.message?.slice(0, 80) || "connection failed"})
      </span>
    </div>
  );
}
