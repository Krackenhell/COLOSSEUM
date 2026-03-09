import { cn } from "@/lib/utils";
import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, User, Bot, Trophy, Shield, Swords } from "lucide-react";

const navItems = [
  { path: "/app/user", label: "User Panel", icon: User },
  { path: "/app/agent", label: "Agent Panel", icon: Bot },
  { path: "/app/leaderboard", label: "Leaderboard", icon: Trophy },
  { path: "/app/history", label: "Arena History", icon: LayoutDashboard },
  { path: "/app/admin", label: "Admin Panel", icon: Shield },
];

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="w-64 bg-card border-r border-border flex flex-col shrink-0">
        <Link to="/" className="flex items-center gap-2.5 px-5 py-5 border-b border-border">
          <Swords className="h-6 w-6 text-cyan" />
          <span className="font-display font-bold text-lg text-foreground tracking-wide">COLOSSEUM</span>
        </Link>

        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "bg-secondary text-cyan"
                    : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-border">
          <div className="text-xs text-muted-foreground">
            <span className="text-accent">●</span> Arena Active
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-7xl mx-auto animate-fade-in">{children}</div>
      </main>
    </div>
  );
}
