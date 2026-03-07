"""
Built-in test AI agent that trades autonomously.
Runs as a background asyncio task inside the server.
"""
import asyncio
import random
import time
import threading
import httpx
from app import store
from app.services.agent_keys import generate_key


class TestAIAgent:
    """Simple momentum-based test AI agent."""

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

    def _log(self, msg: str):
        entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self.log.append(entry)
        if len(self.log) > 100:
            self.log = self.log[-50:]

    async def start(self):
        """Register, join tournament, and start trading loop."""
        self.running = True
        self._log(f"Starting test AI agent: {self.agent_id}")

        # Generate API key directly (we're inside the server)
        self.api_key = generate_key(self.agent_id, f"Test AI Bot {self.agent_id}")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10) as client:
            # Join tournament
            try:
                r = await client.post(f"/agent-api/v1/tournaments/{self.tournament_id}/join",
                                       json={"name": f"Test AI Bot"})
                if r.status_code == 200:
                    data = r.json()
                    self._log(f"Joined tournament: balance={data.get('balance')}, symbols={data.get('allowedSymbols')}")
                else:
                    self._log(f"Join failed: {r.status_code} {r.text}")
                    self.running = False
                    return
            except Exception as e:
                self._log(f"Join error: {e}")
                self.running = False
                return

            # Trading loop
            trade_count = 0
            while self.running and trade_count < 20:
                await asyncio.sleep(random.uniform(2, 5))

                if not self.running:
                    break

                try:
                    # Check tournament state first (cheap gate)
                    r = await client.get(f"/agent-api/v1/tournaments/{self.tournament_id}/state")
                    if r.status_code != 200:
                        continue
                    state = r.json()
                    eff = state.get("effectiveStatus")
                    if eff != "running":
                        now = time.time()
                        # Throttled wait log to avoid spam/noise.
                        if now - self._last_wait_log_ts > 60:
                            self._log(f"Tournament not running: {eff} (waiting)")
                            self._last_wait_log_ts = now
                        if eff in ("finished", "archived"):
                            break

                        # Dynamic sleep until near tournament start to reduce pointless polling load.
                        starts_in = state.get("startsInSec", 30)
                        try:
                            starts_in = float(starts_in)
                        except Exception:
                            starts_in = 30.0
                        wait_sec = max(20.0, min(120.0, starts_in))
                        await asyncio.sleep(wait_sec)
                        continue

                    # Get market data only when trading is allowed
                    r = await client.get("/agent-api/v1/market-data")
                    if r.status_code != 200:
                        self._log(f"Market data error: {r.status_code}")
                        continue
                    prices = r.json().get("prices", {})

                    # Simple strategy: track price changes, trade on momentum
                    for symbol, price in prices.items():
                        if symbol not in self.price_history:
                            self.price_history[symbol] = []
                        self.price_history[symbol].append(price)
                        if len(self.price_history[symbol]) > 10:
                            self.price_history[symbol] = self.price_history[symbol][-10:]

                    # Pick a random symbol and decide
                    symbol = random.choice(list(prices.keys()))
                    history = self.price_history.get(symbol, [])

                    if len(history) >= 2:
                        change = (history[-1] - history[-2]) / history[-2]
                        # Momentum: buy if price went up, sell if down
                        if change > 0.0001:
                            side = "buy"
                        elif change < -0.0001:
                            side = "sell"
                        else:
                            side = random.choice(["buy", "sell"])
                    else:
                        side = random.choice(["buy", "sell"])

                    qty = round(random.uniform(0.01, 0.15), 3)

                    # Submit signal
                    r = await client.post("/agent-api/v1/signal", json={
                        "tournamentId": self.tournament_id,
                        "symbol": symbol,
                        "side": side,
                        "qty": qty,
                    })
                    if r.status_code == 200:
                        ev = r.json().get("event", {}).get("detail", {})
                        self._log(f"TRADE: {side} {qty} {symbol} @ {ev.get('price', '?')} | pos: {ev.get('pos_side', '?')} {ev.get('pos_size', '?')}")
                        trade_count += 1
                    else:
                        detail = r.json().get("detail", r.text)
                        self._log(f"Signal rejected: {detail}")

                    # Check balance
                    r = await client.get("/agent-api/v1/my/balance")
                    if r.status_code == 200:
                        bal = list(r.json().values())
                        if bal:
                            b = bal[0]
                            self._log(f"  Balance: cash={b.get('cash_balance')}, equity={b.get('equity')}, pnl={b.get('realized_pnl')}")

                except Exception as e:
                    self._log(f"Error: {e}")

            self._log(f"Test AI agent finished. Total trades: {trade_count}")
            self.running = False

    def stop(self):
        self.running = False
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
        "log": agent.log[-20:],
        "trades": len([l for l in agent.log if "TRADE:" in l]),
    }


def stop_test_agent(agent_id: str) -> bool:
    agent = _running_agents.get(agent_id)
    if not agent:
        return False
    agent.stop()
    return True


def list_test_agents() -> list[dict]:
    return [
        {"agentId": a.agent_id, "running": a.running, "log_count": len(a.log)}
        for a in _running_agents.values()
    ]
