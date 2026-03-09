import { cn } from "@/lib/utils";

interface RomanBadgeProps {
  label: string;
  variant?: "champion" | "veteran" | "elite" | "warrior" | "recruit";
  className?: string;
}

const variantStyles = {
  champion: "bg-accent/20 text-accent border-accent/30",
  veteran: "bg-cyan/20 text-cyan border-cyan/30",
  elite: "bg-primary/20 text-primary border-primary/30",
  warrior: "bg-secondary text-foreground border-border",
  recruit: "bg-muted text-muted-foreground border-border",
};

export function RomanBadge({ label, variant = "recruit", className }: RomanBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded border tracking-wide uppercase",
        variantStyles[variant],
        className
      )}
    >
      {variant === "champion" && "⚜ "}
      {variant === "veteran" && "⚔ "}
      {variant === "elite" && "🛡 "}
      {label}
    </span>
  );
}
