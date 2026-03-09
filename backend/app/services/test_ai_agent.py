"""
Built-in test AI agent that trades autonomously.
Runs as a background asyncio task inside the server.
"""
import asyncio
import random
import time
import math
import threading
import httpx
from app import store
from app.services.agent_keys import generate_key


class TestAIAgent:
    """Simple momentum-based test AI agent with dynamic leverage."""

    def __init__(self, base_url: str, tournament_id: str):
        self.base_url = base_url
        self.tournament_id = tournament_id
        self.agent_id = f"test-ai-{random.randint(1000,9999)}"
        self.api_key = None
        self.running = False
        self._task = None
        self.log = []
        self.price_history: dict[str, list[float]] = {}
        self._last_wait_log_ts = 0.0
        self.status = "initializing"
        self.trades_executed = 0

    def _log(self, msg: str):
        entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self.log.append(entry)
        if len(self.log) > 200:
            self.log = self.log[-100:]

    def _compute_leverage(self, symbol: str, max_leverage: float) -> float:
        """Dynamic leverage based on recent volatility. High vol → lower leverage."""
        history = self.price_history.get(symbol, [])
        if len(history) < 3:
            # Not enough data: use moderate random leverage
            return round(random.uniform(2.0, min(5.0, max_leverage)), 1)

        # Compute recent volatility (std of returns)
        returns = [(history[i] - history[i-1]) / history[i-1] for i in range(1, len(history))]
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        vol = math.sqrt(variance) if variance > 0 else 0.001

        # Inverse volatility scaling: high vol → low leverage
        # vol ~ 0.001 → lev ~max, vol ~ 0.01 → lev ~2
        raw = min(max_leverage, max(1.0, 0.01 / (vol + 0.001)))
        # Add small randomness
        jitter = random.uniform(-1.0, 1.0)
        lev = max(1.0, min(max_leverage, raw + jitter))
        return round(lev, 1)

    async def start(self):
        """Register, join tournament, and start trading loop."""
        self.running = True
        self.status = "starting"
        self._log(f"Starting test AI agent: {self.agent_id}")

        # Generate API key directly (we're inside the server)
        self.api_key = generate_key(self.agent_id, f"Test AI Bot {self.agent_id}")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10) as client:
            # Join tournament — retry loop for scheduled tournaments
            joined = False
            for attempt in range(60):  # wait up to ~5min for tournament to accept joins
                if not self.running:
                    return
                try:
                    r = await client.post(f"/agent-api/v1/tournaments/{self.tournament_id}/join",
                                           json={"name": f"Test AI Bot"})
                    if r.status_code == 200:
                        data = r.json()
                        self._log(f"Joined tournament: balance={data.get('balance')}, symbols={data.get('allowedSymbols')}")
                        joined = True
                        break
                    elif r.status_code == 400 and "Registration closed" in r.text:
                        # Tournament already running — register directly in store as fallback
                        self._log(f"Late join attempt {attempt+1}: trying direct registration...")
                        if self._direct_register():
                            joined = True
                            break
                        await asyncio.sleep(5)
                    else:
                        self._log(f"Join attempt {attempt+1} failed: {r.status_code} {r.text[:100]}")
                        await asyncio.sleep(5)
                except Exception as e:
                    self._log(f"Join error (attempt {attempt+1}): {e}")
                    await asyncio.sleep(5)

            if not joined:
                self._log("Failed to join tournament after retries. Stopping.")
                self.running = False
                self.status = "failed"
                return

            self.status = "trading"

            # Trading loop — runs until tournament ends or stopped
            while self.running:
                await asyncio.sleep(random.uniform(2, 5))

                if not self.running:
                    break

                try:
                    # Check tournament state
                    r = await client.get(f"/agent-api/v1/tournaments/{self.tournament_id}/state")
                    if r.status_code != 200:
                        continue
                    state = r.json()
                    eff = state.get("effectiveStatus")
                    max_leverage = state.get("leverage", 10.0)

                    if eff != "running":
                        now = time.time()
                        if now - self._last_wait_log_ts > 60:
                            self._log(f"Tournament not running: {eff} (waiting)")
                            self._last_wait_log_ts = now
                            self.status = f"waiting ({eff})"
                        if eff in ("finished", "archived"):
                            break

                        starts_in = state.get("startsInSec", 30)
                        try:
                            starts_in = float(starts_in)
                        except Exception:
                            starts_in = 30.0
                        wait_sec = max(5.0, min(120.0, starts_in * 0.8))
                        await asyncio.sleep(wait_sec)
                        continue

                    self.status = "trading"

                    # Get market data
                    r = await client.get("/agent-api/v1/market-data")
                    if r.status_code != 200:
                        self._log(f"Market data error: {r.status_code}")
                        continue
                    prices = r.json().get("prices", {})

                    # Track price history
                    for symbol, price in prices.items():
                        if symbol not in self.price_history:
                            self.price_history[symbol] = []
                        self.price_history[symbol].append(price)
                        if len(self.price_history[symbol]) > 20:
                            self.price_history[symbol] = self.price_history[symbol][-20:]

                    # Pick a symbol and decide
                    symbol = random.choice(list(prices.keys()))
                    history = self.price_history.get(symbol, [])

                    if len(history) >= 2:
                        change = (history[-1] - history[-2]) / history[-2]
                        if change > 0.0001:
                            side = "buy"
                        elif change < -0.0001:
                            side = "sell"
                        else:
                            side = random.choice(["buy", "sell"])
                    else:
                        side = random.choice(["buy", "sell"])

                    qty = round(random.uniform(0.01, 0.15), 3)
                    leverage = self._compute_leverage(symbol, max_leverage)

                    # Submit signal with agent-chosen leverage
                    r = await client.post("/agent-api/v1/signal", json={
                        "tournamentId": self.tournament_id,
                        "symbol": symbol,
                        "side": side,
                        "qty": qty,
                        "leverage": leverage,
                    })
                    if r.status_code == 200:
                        ev = r.json().get("event", {}).get("detail", {})
                        self._log(f"TRADE: {side} {qty} {symbol} @ {ev.get('price', '?')} lev={leverage}x | pos: {ev.get('pos_side', '?')} {ev.get('pos_size', '?')}")
                        self.trades_executed += 1
                    else:
                        detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text[:100]
                        self._log(f"Signal rejected: {detail}")

                    # Check balance periodically
                    if self.trades_executed % 3 == 0:
                        r = await client.get("/agent-api/v1/my/balance")
                        if r.status_code == 200:
                            bal = list(r.json().values())
                            if bal:
                                b = bal[0]
                                self._log(f"  Balance: cash={b.get('cash_balance')}, equity={b.get('equity')}, pnl={b.get('realized_pnl')}")

                except Exception as e:
                    self._log(f"Error: {e}")

            self._log(f"Test AI agent finished. Total trades: {self.trades_executed}")
            self.running = False
            self.status = "finished"

    def _direct_register(self) -> bool:
        """Fallback: register agent directly in store when API join rejects (tournament already running)."""
        try:
            t = store.tournaments.get(self.tournament_id)
            if not t:
                return False
            from app.types import AgentState
            if self.agent_id not in store.agents.get(self.tournament_id, {}):
                state = AgentState(
                    agentId=self.agent_id, name=f"Test AI Bot {self.agent_id}",
                    tournamentId=self.tournament_id,
                    cash_balance=t.startingBalance, starting_balance=t.startingBalance,
                    equity=t.startingBalance,
                )
                store.agents.setdefault(self.tournament_id, {})[self.agent_id] = state
                store.user_agent_tournament[self.agent_id] = self.tournament_id
            store.agents[self.tournament_id][self.agent_id].connected = True
            self._log("Registered via direct store access (late join)")
            return True
        except Exception as e:
            self._log(f"Direct register failed: {e}")
            return False

    def stop(self):
        self.running = False
        self.status = "stopping"
        self._log("Stopping...")


# Global registry of running test agents
_running_agents: dict[str, TestAIAgent] = {}


def start_test_agent(base_url: str, tournament_id: str) -> dict:
    """Start a test AI agent for a tournament. Returns agent info."""
    agent = TestAIAgent(base_url, tournament_id)
    _running_agents[agent.agent_id] = agent

    def _thread_run():
        try:
            asyncio.run(agent.start())
        except Exception as e:
            agent._log(f"Fatal error: {e}")
            agent.running = False
            agent.status = "crashed"

    t = threading.Thread(target=_thread_run, daemon=True)
    t.start()
    agent._task = t

    return {
        "agentId": agent.agent_id,
        "api_key": agent.api_key or "(generating...)",
        "status": "starting",
    }


def get_test_agent_status(agent_id: str) -> dict | None:
    agent = _running_agents.get(agent_id)
    if not agent:
        return None
    return {
        "agentId": agent.agent_id,
        "running": agent.running,
        "status": agent.status,
        "log": agent.log[-20:],
        "trades": agent.trades_executed,
    }


def stop_test_agent(agent_id: str) -> bool:
    agent = _running_agents.get(agent_id)
    if not agent:
        return False
    agent.stop()
    return True


def list_test_agents() -> list[dict]:
    return [
        {"agentId": a.agent_id, "running": a.running, "status": a.status, "log_count": len(a.log), "trades": a.trades_executed}
        for a in _running_agents.values()
    ]
