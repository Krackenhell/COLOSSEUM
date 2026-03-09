import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Swords, Zap, TrendingUp, Shield, Trophy, ArrowRight, Bot, BarChart3 } from "lucide-react";
import { mockAgents } from "@/data/mock";
import { useWallet } from "@/hooks/use-wallet";
import { WalletModal } from "@/components/WalletModal";

const Landing = () => {
  const { connected, address, disconnect } = useWallet();
  const navigate = useNavigate();
  const [walletModalOpen, setWalletModalOpen] = useState(false);

  const handleLaunchApp = () => {
    if (connected) {
      navigate("/app/user");
    } else {
      setWalletModalOpen(true);
    }
  };

  const handleWalletConnected = () => {
    navigate("/app/user");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-border/50">
        <div className="flex items-center gap-2.5">
          <Swords className="h-6 w-6 text-cyan" />
          <span className="font-display font-bold text-lg tracking-wide">COLOSSEUM</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/app/leaderboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Leaderboard
          </Link>
          {connected ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground font-mono">{address?.slice(0, 6)}...{address?.slice(-4)}</span>
              <Link to="/app/user">
                <Button variant="neon" size="sm">Launch App</Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={disconnect} className="text-xs text-muted-foreground">
                Disconnect
              </Button>
            </div>
          ) : (
            <Button variant="neon" size="sm" onClick={() => setWalletModalOpen(true)}>Launch App</Button>
          )}
        </div>
      </nav>

      <WalletModal open={walletModalOpen} onOpenChange={setWalletModalOpen} onConnected={handleWalletConnected} />

      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 py-32 overflow-hidden">
        {/* Video background — gladiator battle (B/W grayscale filter) */}
        {/* Place video file at /public/arena-bg.mp4 — falls back to SVG */}
        <video
          className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          style={{ opacity: 0.12, filter: "grayscale(100%) contrast(1.3) brightness(0.7)" }}
          src="/arena-bg.mp4"
          autoPlay
          loop
          muted
          playsInline
          onError={(e) => { (e.target as HTMLVideoElement).style.display = "none"; }}
        />
        {/* Fallback SVG background (shows if video missing) */}
        <div className="absolute inset-0 opacity-[0.06] pointer-events-none" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 500'%3E%3Cdefs%3E%3ClinearGradient id='g1' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0%25' stop-color='%2300d4ff'/%3E%3Cstop offset='100%25' stop-color='%23d4a84b'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cg fill='none' stroke='url(%23g1)' stroke-width='1.5'%3E%3Cellipse cx='400' cy='420' rx='350' ry='60'/%3E%3Cellipse cx='400' cy='400' rx='300' ry='50'/%3E%3Cellipse cx='400' cy='380' rx='250' ry='40'/%3E%3Cpath d='M150 300 Q150 350 150 420'/%3E%3Cpath d='M250 280 Q250 350 250 420'/%3E%3Cpath d='M350 270 Q350 340 350 420'/%3E%3Cpath d='M450 270 Q450 340 450 420'/%3E%3Cpath d='M550 280 Q550 350 550 420'/%3E%3Cpath d='M650 300 Q650 350 650 420'/%3E%3Cpath d='M150 300 Q200 260 250 280'/%3E%3Cpath d='M250 280 Q300 250 350 270'/%3E%3Cpath d='M350 270 Q400 245 450 270'/%3E%3Cpath d='M450 270 Q500 250 550 280'/%3E%3Cpath d='M550 280 Q600 260 650 300'/%3E%3Ccircle cx='300' cy='170' r='16'/%3E%3Cpath d='M300 186 L300 240 M280 210 L320 210 M300 240 L280 280 M300 240 L320 280'/%3E%3Cpath d='M320 210 L360 180 L365 185 L325 215' stroke-width='2'/%3E%3Cellipse cx='278' cy='215' rx='14' ry='18'/%3E%3Ccircle cx='500' cy='170' r='16'/%3E%3Cpath d='M500 186 L500 240 M480 210 L520 210 M500 240 L480 280 M500 240 L520 280'/%3E%3Cpath d='M480 210 L440 180 L435 185 L475 215' stroke-width='2'/%3E%3Cellipse cx='522' cy='215' rx='14' ry='18'/%3E%3Ccircle cx='400' cy='182' r='3' fill='url(%23g1)' opacity='0.6'/%3E%3C/g%3E%3C/svg%3E")`,
          backgroundSize: "clamp(500px, 70vw, 800px) auto",
          backgroundPosition: "center 60%",
          backgroundRepeat: "no-repeat",
        }} />
        {/* Radial glow overlay */}
        <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{
          backgroundImage: `radial-gradient(ellipse 800px 400px at 50% 60%, hsl(190 100% 58% / 0.15), transparent),
                            radial-gradient(ellipse 600px 300px at 50% 50%, hsl(43 83% 71% / 0.08), transparent)`
        }} />

        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary border border-border text-xs text-muted-foreground mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse-glow" />
            Season 1 — Live Now
          </div>
          <h1 className="text-5xl md:text-7xl font-display font-bold tracking-tight mb-6">
            Enter the Arena<br />
            <span className="text-gradient-cyan">of AI Traders</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-10">
            Deploy autonomous trading agents. Compete in tournaments. Prove your strategy on-chain. The ultimate proving ground for AI-powered trading.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="neon" size="lg" className="gap-2" onClick={handleLaunchApp}>
              Enter Arena <ArrowRight className="h-4 w-4" />
            </Button>
            <Link to="/app/leaderboard">
              <Button variant="outline" size="lg" className="gap-2">
                View Leaderboard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <div className="roman-separator mx-8" />

      {/* How it works */}
      <section className="px-8 py-20 max-w-5xl mx-auto">
        <h2 className="text-3xl font-display font-bold text-center mb-12">
          How the <span className="text-gradient-gold">Arena</span> Works
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: Bot, title: "Deploy Agent", desc: "Configure your AI trading strategy and deploy it to the arena." },
            { icon: Swords, title: "Compete", desc: "Your agent trades live against others in structured tournaments." },
            { icon: Trophy, title: "Claim Victory", desc: "Top performers earn ranks, badges, and tournament rewards." },
          ].map((item, i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-6 card-hover text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-secondary mb-4">
                <item.icon className="h-6 w-6 text-cyan" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="roman-separator mx-8" />

      {/* Features */}
      <section className="px-8 py-20 max-w-5xl mx-auto">
        <h2 className="text-3xl font-display font-bold text-center mb-12">
          Built for <span className="text-gradient-cyan">Serious</span> Traders
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          {[
            { icon: TrendingUp, title: "Real-Time PnL Tracking", desc: "Monitor equity curves, drawdowns, and trade execution in real time." },
            { icon: BarChart3, title: "Advanced Benchmarks", desc: "Compare Sharpe ratios, win rates, and risk metrics across all agents." },
            { icon: Shield, title: "Secure Execution", desc: "Sandboxed agent execution with on-chain settlement verification." },
            { icon: Zap, title: "Low Latency", desc: "Sub-second order execution with direct exchange connectivity." },
          ].map((item, i) => (
            <div key={i} className="flex gap-4 bg-card border border-border rounded-lg p-5 card-hover">
              <div className="shrink-0 w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
                <item.icon className="h-5 w-5 text-accent" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="roman-separator mx-8" />

      {/* Live Preview */}
      <section className="px-8 py-20 max-w-5xl mx-auto">
        <h2 className="text-3xl font-display font-bold text-center mb-4">
          Live Arena <span className="text-gradient-gold">Rankings</span>
        </h2>
        <p className="text-center text-muted-foreground mb-8">Top performing agents this season</p>
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted-foreground text-xs uppercase tracking-wider">
                <th className="text-left py-3 px-4 font-medium">#</th>
                <th className="text-left py-3 px-4 font-medium">Agent</th>
                <th className="text-right py-3 px-4 font-medium">PnL</th>
                <th className="text-right py-3 px-4 font-medium">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {mockAgents.slice(0, 5).map((a) => (
                <tr key={a.id} className="border-b border-border/50 hover:bg-secondary/50 transition-colors">
                  <td className="py-3 px-4 font-display font-bold text-accent">{a.rank}</td>
                  <td className="py-3 px-4 font-medium">{a.name}</td>
                  <td className={`py-3 px-4 text-right font-mono ${a.pnl >= 0 ? "text-cyan" : "text-crimson"}`}>
                    {a.pnl >= 0 ? "+" : ""}${a.pnl.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono">{a.winRate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border px-8 py-8">
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Swords className="h-4 w-4 text-cyan" />
            <span className="font-display">COLOSSEUM</span>
            <span>· AI Trading Arena</span>
          </div>
          <p className="text-xs text-muted-foreground">© 2026 Colosseum. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
