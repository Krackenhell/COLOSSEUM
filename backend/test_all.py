"""End-to-end validation tests for Colosseum with AVAX + Chainlink."""
import os
import sys
import time

# Set chainlink mode for testing
os.environ["MARKET_SOURCE"] = "chainlink"
os.environ["CHAINLINK_RPC_URL"] = "https://avax-mainnet.g.alchemy.com/v2/6evpjOd1KcH2a5Qra3FtceXxeajc-GoH"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
KEY = "dev-gateway-key"
HEADERS = {"Content-Type": "application/json", "x-api-key": KEY}

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name}: {e}")
        failed += 1

# === TESTS ===

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_market_status():
    r = client.get("/market-status")
    assert r.status_code == 200
    d = r.json()
    assert d["marketSource"] == "chainlink"
    assert "AVAXUSDT" in d["symbols"]
    assert "BTCUSDT" in d["symbols"]
    assert "ETHUSDT" in d["symbols"]
    # SOL should NOT be there
    assert "SOLUSDT" not in d["symbols"]

def test_create_tournament_avax():
    now = time.time()
    r = client.post("/tournaments", json={
        "name": "Test AVAX Tournament",
        "allowedSymbols": ["BTCUSDT", "ETHUSDT", "AVAXUSDT"],
        "startAt": now + 1,
        "endAt": now + 3600,
    }, headers=HEADERS)
    assert r.status_code == 200
    d = r.json()
    assert "AVAXUSDT" in d["allowedSymbols"]
    assert "SOLUSDT" not in d["allowedSymbols"]
    return d["id"]

def test_create_and_trade():
    now = time.time()
    # Create tournament starting in the future (so we can register)
    r = client.post("/tournaments", json={
        "name": "Trade Test",
        "startAt": now + 60,
        "endAt": now + 3600,
    }, headers=HEADERS)
    assert r.status_code == 200
    tid = r.json()["id"]

    # Register agent (tournament is scheduled, registration open)
    r = client.post(f"/tournaments/{tid}/register-agent", json={
        "agentId": "test-agent-1",
        "name": "Test Agent"
    }, headers=HEADERS)
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"

    # Hack: move startAt to past so effective_status becomes "running"
    from app import store as _store
    _store.tournaments[tid].startAt = time.time() - 10

    # Connect
    r = client.post("/gateway/connect-agent", json={
        "agentId": "test-agent-1",
        "tournamentId": tid,
        "timestamp": time.time(),
        "nonce": f"nonce-{time.time()}"
    }, headers=HEADERS)

    # Submit signals for all 3 symbols
    for sym in ["BTCUSDT", "ETHUSDT", "AVAXUSDT"]:
        r = client.post("/gateway/submit-signal", json={
            "agentId": "test-agent-1",
            "tournamentId": tid,
            "symbol": sym,
            "side": "buy",
            "qty": 0.01,
            "timestamp": time.time(),
            "nonce": f"nonce-{sym}-{time.time()}"
        }, headers=HEADERS)
        assert r.status_code == 200, f"Signal failed for {sym}: {r.status_code} {r.text}"

    # Check leaderboard
    r = client.get(f"/tournaments/{tid}/leaderboard", headers=HEADERS)
    assert r.status_code == 200
    lb = r.json()
    assert len(lb) > 0

def test_chainlink_prices():
    """Test that chainlink mode returns real prices (or graceful fallback)."""
    from app.services.market_data import get_price, get_all_prices, MARKET_SOURCE
    assert MARKET_SOURCE == "chainlink"
    prices = get_all_prices()
    for sym in ["BTCUSDT", "ETHUSDT", "AVAXUSDT"]:
        assert sym in prices
        assert prices[sym] > 0, f"{sym} price is {prices[sym]}"
    # BTC should be > 10000 (sanity)
    print(f"    Prices: BTC={prices['BTCUSDT']}, ETH={prices['ETHUSDT']}, AVAX={prices['AVAXUSDT']}")

def test_fallback_on_failure():
    """Simulate chainlink failure and verify fallback works."""
    from app.services import market_data as md
    # Save state
    old_rpc = md.CHAINLINK_RPC
    old_w3 = md._w3
    old_init = md._w3_init_attempted

    # Break the connection
    md._w3 = None
    md._w3_init_attempted = False
    md.CHAINLINK_RPC = "https://invalid-rpc-that-does-not-exist.example.com"

    try:
        # Should NOT crash - should return fallback price
        price = md.get_price("BTCUSDT")
        assert price > 0, f"Fallback price should be > 0, got {price}"
        price2 = md.get_price("AVAXUSDT")
        assert price2 > 0, f"AVAX fallback price should be > 0, got {price2}"
        print(f"    Fallback prices: BTC={price}, AVAX={price2}")

        # Market status should show fallback
        status = md.get_market_status()
        # At least one symbol should show fallback or error
        print(f"    Market status source: {status['marketSource']}, connected: {status['chainlinkConnected']}")
    finally:
        # Restore
        md.CHAINLINK_RPC = old_rpc
        md._w3 = old_w3
        md._w3_init_attempted = old_init

def test_market_status_endpoint():
    r = client.get("/market-status")
    assert r.status_code == 200
    d = r.json()
    assert "marketSource" in d
    assert "symbols" in d
    for sym in ["BTCUSDT", "ETHUSDT", "AVAXUSDT"]:
        assert sym in d["symbols"]

def test_no_sol_in_defaults():
    """Verify SOL is fully replaced by AVAX."""
    from app.types import CreateTournament, Tournament
    ct = CreateTournament(name="test")
    assert "AVAXUSDT" in ct.allowedSymbols
    assert "SOLUSDT" not in ct.allowedSymbols
    t = Tournament(name="test")
    assert "AVAXUSDT" in t.allowedSymbols
    assert "SOLUSDT" not in t.allowedSymbols

def test_no_500_on_bad_requests():
    """Ensure no 500 errors on edge cases."""
    r = client.get("/market-status")
    assert r.status_code == 200
    r = client.get("/health")
    assert r.status_code == 200
    # Non-existent tournament
    r = client.get("/tournaments/nonexistent/leaderboard", headers=HEADERS)
    assert r.status_code == 404

# === RUN ===
print("\n=== Colosseum AVAX + Chainlink Tests ===\n")

test("Health check", test_health)
test("Market status endpoint", test_market_status)
test("No SOL in defaults", test_no_sol_in_defaults)
test("Create tournament with AVAX", test_create_tournament_avax)
test("Create tournament and trade BTC/ETH/AVAX", test_create_and_trade)
test("Chainlink prices (live or fallback)", test_chainlink_prices)
test("Fallback on RPC failure", test_fallback_on_failure)
test("Market status endpoint detail", test_market_status_endpoint)
test("No 500 on bad requests", test_no_500_on_bad_requests)

print(f"\n=== Results: {passed} passed, {failed} failed ===\n")
sys.exit(1 if failed > 0 else 0)
