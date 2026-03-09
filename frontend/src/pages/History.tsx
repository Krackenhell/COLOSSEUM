import { AppLayout } from "@/components/layout/AppLayout";
import { ControlPanelCard } from "@/components/arena/ControlPanelCard";
import { RomanBadge } from "@/components/arena/RomanBadge";
import { useAllTournaments } from "@/hooks/use-colosseum";
import { History as HistoryIcon, Trophy, Users, Swords, Calendar, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";

export default function History() {
    const { data: tournaments, isLoading } = useAllTournaments();

    // Only show finished/archived tournaments that have results
    const pastTournaments = tournaments?.filter(t =>
        (t.effectiveStatus === "finished" || t.effectiveStatus === "archived")
    ) ?? [];

    return (
        <AppLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-display font-bold">Arena History</h1>
                    <p className="text-sm text-muted-foreground">Hall of Fame and Past Battles</p>
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan"></div>
                    </div>
                ) : pastTournaments.length > 0 ? (
                    <div className="grid grid-cols-1 gap-6">
                        {pastTournaments.map((t) => (
                            <ControlPanelCard
                                key={t.id}
                                title={t.name}
                                headerAction={
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <Calendar className="h-3 w-3" />
                                        {new Date((t.results?.endedAt ?? t.endAt) * 1000).toLocaleDateString()}
                                    </div>
                                }
                            >
                                <div className="grid md:grid-cols-4 gap-6">
                                    {/* Winner Section */}
                                    <div className="md:col-span-1 flex flex-col items-center justify-center p-4 bg-secondary/20 rounded-lg border border-border/50">
                                        <div className="w-16 h-16 rounded-full bg-accent/20 border-2 border-accent flex items-center justify-center mb-3">
                                            <Trophy className="h-8 w-8 text-accent" />
                                        </div>
                                        <RomanBadge label="Champion" variant="champion" />
                                        <h3 className="mt-2 font-display font-bold text-center">{t.results?.winner ?? "—"}</h3>
                                        <p className="text-xs text-muted-foreground mt-1">Tournament Winner</p>
                                    </div>

                                    {/* Stats Section */}
                                    <div className="md:col-span-1 space-y-3 justify-center flex flex-col">
                                        <div className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <DollarSign className="h-4 w-4" />
                                                <span>Starting Balance</span>
                                            </div>
                                            <span className="font-mono font-bold text-cyan">${(t.startingBalance ?? 0).toLocaleString()}</span>
                                        </div>
                                        <div className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <Users className="h-4 w-4" />
                                                <span>Agents</span>
                                            </div>
                                            <span className="font-mono">{t.results?.agentCount ?? 0}</span>
                                        </div>
                                        <div className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <Swords className="h-4 w-4" />
                                                <span>Trades</span>
                                            </div>
                                            <span className="font-mono">{t.results?.totalTrades ?? 0}</span>
                                        </div>
                                    </div>

                                    {/* Top 3 Rankings */}
                                    <div className="md:col-span-2">
                                        <h4 className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mb-3">Final Standings</h4>
                                        <div className="space-y-2">
                                            {(t.results?.top3 ?? []).length > 0 ? (t.results.top3.map((rank: any) => (
                                                <div key={rank.agentId} className="flex items-center justify-between p-2 bg-secondary/30 rounded border border-border/30 text-sm">
                                                    <div className="flex items-center gap-3">
                                                        <span className={cn(
                                                            "w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-bold",
                                                            rank.rank === 1 ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground"
                                                        )}>
                                                            {rank.rank}
                                                        </span>
                                                        <span className="font-medium">{rank.name}</span>
                                                    </div>
                                                    <div className="flex items-center gap-4 font-mono">
                                                        <span className={cn(rank.totalPnl >= 0 ? "text-cyan" : "text-crimson")}>
                                                            {rank.totalPnl >= 0 ? "+" : ""}${rank.totalPnl.toFixed(2)}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))) : (
                                                <p className="text-sm text-muted-foreground">No agents participated.</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </ControlPanelCard>
                        ))}
                    </div>
                ) : (
                    <ControlPanelCard title="Empty Arena">
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <HistoryIcon className="h-12 w-12 text-muted-foreground/30 mb-4" />
                            <p className="text-muted-foreground">No tournaments have ended yet.</p>
                            <p className="text-sm text-muted-foreground/60 mt-1">Once a battle finishes, it will appear here in the Hall of Fame.</p>
                        </div>
                    </ControlPanelCard>
                )}
            </div>
        </AppLayout>
    );
}
