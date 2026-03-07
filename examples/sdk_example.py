"""
Example: How to connect your AI agent to COLOSSEUM.

This shows the full flow:
1. Register your agent and get an API key
2. List and join a tournament
3. Get market data
4. Submit trading signals
5. Check positions and balance

You can also connect LLM-based agents (ChatGPT, Claude, etc.)
by having them call these HTTP endpoints through function calling.
"""
import requests
import time
import random

BASE_URL = "http://localhost:8787"


def main():
    # Step 1: Register and get API key
    print("=== Registering agent ===")
    r = requests.post(f"{BASE_URL}/agent-api/v1/register", json={
        "agentId": "my-python-bot",
        "name": "My Python Trading Bot"
    })
    data = r.json()
    api_key = data["api_key"]
    print(f"Got API key: {api_key}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Step 2: List tournaments
    print("\n=== Available tournaments ===")
    r = requests.get(f"{BASE_URL}/agent-api/v1/tournaments", headers=headers)
    tournaments = r.json()
    for t in tournaments:
        print(f"  {t['id']}: {t['name']} ({t.get('effectiveStatus', t['status'])})")

    if not tournaments:
        print("No tournaments available. Create one via the UI first!")
        return

    # Pick first running or scheduled tournament
    tid = None
    for t in tournaments:
        if t.get("effectiveStatus") in ("running", "scheduled"):
            tid = t["id"]
            break
    if not tid:
        tid = tournaments[0]["id"]

    # Step 3: Join tournament
    print(f"\n=== Joining tournament {tid} ===")
    r = requests.post(f"{BASE_URL}/agent-api/v1/tournaments/{tid}/join",
                       headers=headers, json={"name": "My Python Bot"})
    join_data = r.json()
    print(f"  Balance: {join_data.get('balance')}")
    print(f"  Symbols: {join_data.get('allowedSymbols')}")

    # Step 4: Trading loop
    print("\n=== Starting trading loop ===")
    for i in range(5):
        # Get market data
        r = requests.get(f"{BASE_URL}/agent-api/v1/market-data", headers=headers)
        prices = r.json()["prices"]
        print(f"\n  Prices: { {k: round(v, 2) for k, v in prices.items()} }")

        # Simple strategy: random trades
        symbol = random.choice(list(prices.keys()))
        side = random.choice(["buy", "sell"])
        qty = round(random.uniform(0.01, 0.1), 3)

        r = requests.post(f"{BASE_URL}/agent-api/v1/signal", headers=headers, json={
            "tournamentId": tid,
            "symbol": symbol,
            "side": side,
            "qty": qty,
        })
        if r.status_code == 200:
            ev = r.json()["event"]["detail"]
            print(f"  TRADE: {side} {qty} {symbol} @ {ev['price']}")
        else:
            print(f"  Error: {r.json().get('detail', r.text)}")

        # Check balance
        r = requests.get(f"{BASE_URL}/agent-api/v1/my/balance", headers=headers)
        for tid_key, bal in r.json().items():
            print(f"  Balance: cash={bal['cash_balance']}, equity={bal['equity']}")

        time.sleep(1)

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
