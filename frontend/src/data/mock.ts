export const mockAgents = [
  { id: 1, name: "Gladiator Alpha", rank: 1, pnl: 12847.32, pnlPercent: 28.4, winRate: 73.2, trades: 1284, equity: 57420.00, status: "active", strategy: "Momentum Scalper", badge: "Champion" },
  { id: 2, name: "Centurion V2", rank: 2, pnl: 9231.55, pnlPercent: 21.1, winRate: 68.9, trades: 956, equity: 52810.00, status: "active", strategy: "Mean Reversion", badge: "Veteran" },
  { id: 3, name: "Praetorian Guard", rank: 3, pnl: 7654.20, pnlPercent: 18.3, winRate: 65.4, trades: 1102, equity: 49300.00, status: "active", strategy: "Trend Following", badge: "Elite" },
  { id: 4, name: "Legion IX", rank: 4, pnl: 5421.80, pnlPercent: 14.7, winRate: 61.2, trades: 843, equity: 42150.00, status: "paused", strategy: "Grid Trading", badge: "Warrior" },
  { id: 5, name: "Imperator Bot", rank: 5, pnl: 3210.45, pnlPercent: 9.8, winRate: 58.7, trades: 721, equity: 35890.00, status: "active", strategy: "Arbitrage", badge: "Warrior" },
  { id: 6, name: "Tribune X", rank: 6, pnl: -1245.30, pnlPercent: -4.2, winRate: 45.3, trades: 612, equity: 28410.00, status: "active", strategy: "Breakout", badge: "Recruit" },
  { id: 7, name: "Aquila AI", rank: 7, pnl: -2890.15, pnlPercent: -8.1, winRate: 42.1, trades: 534, equity: 24320.00, status: "stopped", strategy: "Scalping", badge: "Recruit" },
  { id: 8, name: "Spartacus Net", rank: 8, pnl: -4120.60, pnlPercent: -12.3, winRate: 38.9, trades: 445, equity: 19870.00, status: "active", strategy: "DCA", badge: "Recruit" },
];

export const mockPositions = {
  open: [
    { id: 1, pair: "BTC/USDT", side: "LONG", entry: 67234.50, current: 68120.30, size: 0.15, pnl: 132.87, pnlPercent: 1.32, time: "2h 34m" },
    { id: 2, pair: "ETH/USDT", side: "SHORT", entry: 3842.20, current: 3798.10, size: 2.5, pnl: 110.25, pnlPercent: 1.15, time: "1h 12m" },
    { id: 3, pair: "SOL/USDT", side: "LONG", entry: 178.40, current: 175.20, size: 15, pnl: -48.00, pnlPercent: -1.79, time: "45m" },
  ],
  closed: [
    { id: 1, pair: "BTC/USDT", side: "LONG", entry: 66100.00, exit: 67450.00, size: 0.2, pnl: 270.00, pnlPercent: 2.04, duration: "4h 22m" },
    { id: 2, pair: "ETH/USDT", side: "LONG", entry: 3720.00, exit: 3810.00, size: 3, pnl: 270.00, pnlPercent: 2.42, duration: "2h 15m" },
    { id: 3, pair: "DOGE/USDT", side: "SHORT", entry: 0.1842, exit: 0.1790, size: 10000, pnl: 52.00, pnlPercent: 2.82, duration: "1h 45m" },
    { id: 4, pair: "SOL/USDT", side: "LONG", entry: 172.30, exit: 170.10, size: 10, pnl: -22.00, pnlPercent: -1.28, duration: "3h 10m" },
  ],
};

export const mockChartData = Array.from({ length: 30 }, (_, i) => ({
  day: `Mar ${i + 1}`,
  price: 65000 + Math.sin(i * 0.5) * 3000 + Math.random() * 1000,
  volume: 1200 + Math.random() * 800,
}));

export const mockEquityData = Array.from({ length: 30 }, (_, i) => ({
  day: `Mar ${i + 1}`,
  equity: 40000 + i * 450 + Math.sin(i * 0.4) * 2000 + Math.random() * 500,
}));

export const mockEvents = [
  { id: 1, type: "trade", message: "Opened LONG BTC/USDT @ 67,234.50", time: "2 min ago", severity: "info" },
  { id: 2, type: "alert", message: "Stop loss triggered on SOL/USDT", time: "15 min ago", severity: "warning" },
  { id: 3, type: "system", message: "Strategy parameters auto-adjusted", time: "32 min ago", severity: "info" },
  { id: 4, type: "trade", message: "Closed SHORT ETH/USDT +$110.25", time: "1h ago", severity: "success" },
  { id: 5, type: "alert", message: "High volatility detected on BTC", time: "1h 30m ago", severity: "warning" },
  { id: 6, type: "system", message: "Agent restarted successfully", time: "2h ago", severity: "info" },
];

export const mockTournaments = [
  { id: 1, name: "Colosseum Grand Prix I", status: "active", participants: 24, startDate: "2026-03-01", endDate: "2026-03-31", prize: "$50,000" },
  { id: 2, name: "Gladiator League S2", status: "upcoming", participants: 0, startDate: "2026-04-01", endDate: "2026-04-30", prize: "$75,000" },
  { id: 3, name: "Arena Trials: BTC Only", status: "completed", participants: 16, startDate: "2026-02-01", endDate: "2026-02-28", prize: "$25,000" },
];

export const mockLogs = [
  { id: 1, timestamp: "2026-03-09 14:32:01", level: "INFO", message: "Tournament engine started" },
  { id: 2, timestamp: "2026-03-09 14:32:02", level: "INFO", message: "Connected to price feed: Binance WS" },
  { id: 3, timestamp: "2026-03-09 14:32:03", level: "WARN", message: "Agent 'Legion IX' heartbeat delayed 2.3s" },
  { id: 4, timestamp: "2026-03-09 14:32:05", level: "INFO", message: "Order matched: BTC LONG 0.15 @ 67234.50" },
  { id: 5, timestamp: "2026-03-09 14:32:08", level: "ERROR", message: "Agent 'Aquila AI' disconnected — retry in 5s" },
  { id: 6, timestamp: "2026-03-09 14:32:10", level: "INFO", message: "Snapshot saved: 24 agents, 47 open positions" },
  { id: 7, timestamp: "2026-03-09 14:32:15", level: "INFO", message: "PnL recalculation completed in 12ms" },
  { id: 8, timestamp: "2026-03-09 14:32:20", level: "WARN", message: "Rate limit approaching for Bybit API" },
];

export const mockBenchmarkData = mockAgents.slice(0, 5).map(a => ({
  name: a.name,
  pnl: a.pnlPercent,
  winRate: a.winRate,
  sharpe: +(1.2 + Math.random() * 1.5).toFixed(2),
  maxDrawdown: +(5 + Math.random() * 15).toFixed(1),
}));
