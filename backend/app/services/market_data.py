"""Market data adapter: mock (default) or Chainlink via Avalanche C-Chain with robust fallback.

Includes quote snapshot store for quote-based execution."""
import os
import random
import time
import logging
import json
import threading
import uuid

logger = logging.getLogger(__name__)

BASE_PRICES = {
    "BTCUSDT": 67000.0,
    "ETHUSDT": 3500.0,
    "AVAXUSDT": 35.0,
}

# Chainlink price feed addresses on Avalanche C-Chain
CHAINLINK_FEEDS = {
    "BTCUSDT": "0x2779D32d5166BAaa2B2b658333bA7e6Ec0C65743",  # BTC/USD on Avalanche
    "ETHUSDT": "0x976B3D034E162d8bD72D6b9C989d545b839003b0",  # ETH/USD on Avalanche
    "AVAXUSDT": "0x0A77230d17318075983913bC2145DB16C7366156",  # AVAX/USD on Avalanche
}

# Minimal Chainlink AggregatorV3 ABI
AGGREGATOR_ABI = json.loads('[{"inputs":[],"name":"latestRoundData","outputs":[{"name":"roundId","type":"uint80"},{"name":"answer","type":"int256"},{"name":"startedAt","type":"uint256"},{"name":"updatedAt","type":"uint256"},{"name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')

# --- Configuration via env vars ---
MARKET_SOURCE = os.environ.get("MARKET_SOURCE", "mock").lower()
CHAINLINK_RPC = os.environ.get("CHAINLINK_RPC_URL", "")
CHAINLINK_CACHE_TTL = int(os.environ.get("CHAINLINK_CACHE_TTL_SEC", "5"))
CHAINLINK_MAX_STALENESS = int(os.environ.get("CHAINLINK_MAX_STALENESS_SEC", "3600"))
TRADING_MAX_ORACLE_AGE_SEC = int(os.environ.get("TRADING_MAX_ORACLE_AGE_SEC", "60"))
CHAINLINK_STRICT_ONLY = os.environ.get("CHAINLINK_STRICT_ONLY", "0") == "1"

# --- Internal state (thread-safe via GIL for simple dict ops) ---
_lock = threading.Lock()
_mock_prices: dict[str, float] = dict(BASE_PRICES)
_last_good: dict[str, dict] = {}  # symbol -> {"price": float, "ts": float, "source": str}
_chainlink_cache: dict[str, dict] = {}  # symbol -> {"price": float, "ts": float}
_last_error: dict[str, str] = {}  # symbol -> error string
_fallback_active: dict[str, bool] = {}
_chainlink_round_data: dict[str, dict] = {}  # symbol -> {"roundId", "updatedAt", "fetchTs"}
_w3 = None
_w3_init_attempted = False
_decimals_cache: dict[str, int] = {}

# --- Live Exchange state ---
BINANCE_SYMBOLS = {"BTCUSDT": "BTCUSDT", "ETHUSDT": "ETHUSDT", "AVAXUSDT": "AVAXUSDT"}
_exchange_cache: dict[str, dict] = {}  # symbol -> {"price": float, "ts": float, "source": str, "stale": bool}
_exchange_lock = threading.Lock()

# --- Quote snapshot store ---
QUOTE_TTL_SEC = 10
QUOTE_MAX_SIZE = 500
_quote_store: dict[str, dict] = {}  # quoteId -> {"prices": {sym: price}, "ts": float, "freshness": {...}}
_quote_lock = threading.Lock()


COINGECKO_IDS = {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "AVAXUSDT": "avalanche-2"}


def _fetch_live_exchange_prices() -> dict[str, float]:
    """Fetch live prices from CoinGecko (primary) or Binance (fallback). Returns {symbol: price}."""
    import urllib.request
    results = {}
    now = time.time()
    source = "unknown"

    # Try CoinGecko first (no geo-restrictions)
    try:
        ids = ",".join(COINGECKO_IDS.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"User-Agent": "Colosseum/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
        source = "coingecko"
        for our_sym, cg_id in COINGECKO_IDS.items():
            if cg_id in data and "usd" in data[cg_id] and data[cg_id]["usd"] > 0:
                price = float(data[cg_id]["usd"])
                results[our_sym] = price
                with _exchange_lock:
                    _exchange_cache[our_sym] = {"price": price, "ts": now, "source": source, "stale": False}
        if results:
            return results
    except Exception as e:
        logger.warning(f"LiveExchange: CoinGecko failed: {str(e)[:200]}")

    # Fallback: Binance
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        req = urllib.request.Request(url, headers={"User-Agent": "Colosseum/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
        price_map = {item["symbol"]: float(item["price"]) for item in data}
        source = "binance"
        for our_sym, binance_sym in BINANCE_SYMBOLS.items():
            if binance_sym in price_map and price_map[binance_sym] > 0:
                results[our_sym] = price_map[binance_sym]
                with _exchange_lock:
                    _exchange_cache[our_sym] = {"price": price_map[binance_sym], "ts": now, "source": source, "stale": False}
        if results:
            return results
    except Exception as e:
        logger.warning(f"LiveExchange: Binance fallback failed: {str(e)[:200]}")

    # Both failed — mark stale
    with _exchange_lock:
        for sym in BINANCE_SYMBOLS:
            if sym in _exchange_cache:
                _exchange_cache[sym]["stale"] = True
    return results


def _get_exchange_data(symbol: str) -> dict:
    """Get cached exchange data for a symbol, safe for display."""
    with _exchange_lock:
        cached = _exchange_cache.get(symbol)
    if not cached:
        return {"liveExchangePrice": None, "liveExchangeUpdatedAt": None,
                "liveExchangeAgeSec": None, "liveExchangeSource": "binance", "liveExchangeStale": True}
    now = time.time()
    return {
        "liveExchangePrice": round(cached["price"], 4),
        "liveExchangeUpdatedAt": round(cached["ts"], 3),
        "liveExchangeAgeSec": round(now - cached["ts"], 1),
        "liveExchangeSource": cached["source"],
        "liveExchangeStale": cached["stale"],
    }


def _get_web3():
    """Lazy-init Web3 connection. Returns None on any failure."""
    global _w3, _w3_init_attempted
    if _w3 is not None:
        return _w3
    if _w3_init_attempted:
        return None
    _w3_init_attempted = True
    if not CHAINLINK_RPC:
        logger.warning("Chainlink: CHAINLINK_RPC_URL not set, chainlink mode will use fallback")
        return None
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(CHAINLINK_RPC, request_kwargs={"timeout": 5}))
        if w3.is_connected():
            logger.info(f"Chainlink: connected to RPC (Avalanche C-Chain)")
            _w3 = w3
            return _w3
        else:
            logger.warning("Chainlink: Web3 not connected")
    except ImportError:
        logger.warning("Chainlink: web3 package not installed (pip install web3)")
    except Exception as e:
        logger.warning(f"Chainlink: connection failed: {e}")
    return None


def _reset_web3():
    """Reset web3 to allow reconnect on next attempt."""
    global _w3, _w3_init_attempted
    _w3 = None
    _w3_init_attempted = False


def _get_decimals(w3, feed_address: str) -> int:
    """Get decimals for a feed, cached."""
    addr_key = feed_address.lower()
    if addr_key in _decimals_cache:
        return _decimals_cache[addr_key]
    try:
        contract = w3.eth.contract(address=feed_address, abi=AGGREGATOR_ABI)
        d = contract.functions.decimals().call()
        _decimals_cache[addr_key] = d
        return d
    except Exception:
        return 8  # safe default for Chainlink USD feeds


def _fetch_chainlink_price(symbol: str) -> float | None:
    """Fetch price from Chainlink on Avalanche. Returns None on any failure."""
    if symbol not in CHAINLINK_FEEDS:
        return None

    # Check cache first
    now = time.time()
    cached = _chainlink_cache.get(symbol)
    if cached and (now - cached["ts"]) < CHAINLINK_CACHE_TTL:
        return cached["price"]

    w3 = _get_web3()
    if not w3:
        _last_error[symbol] = "Web3 not connected"
        return None

    try:
        feed_address = w3.to_checksum_address(CHAINLINK_FEEDS[symbol])
        contract = w3.eth.contract(address=feed_address, abi=AGGREGATOR_ABI)
        round_id, answer, _, updated_at, _ = contract.functions.latestRoundData().call()

        decimals = _get_decimals(w3, feed_address)
        price = answer / (10 ** decimals)

        if price <= 0:
            _last_error[symbol] = f"Invalid price: {price}"
            logger.warning(f"Chainlink: invalid price for {symbol}: {price}")
            return None

        staleness = now - updated_at
        if staleness > CHAINLINK_MAX_STALENESS:
            _last_error[symbol] = f"Stale: {int(staleness)}s ago"
            logger.warning(f"Chainlink: stale price for {symbol} (updated {int(staleness)}s ago)")
            return None

        # Success - update caches
        _chainlink_cache[symbol] = {"price": price, "ts": now}
        _last_good[symbol] = {"price": price, "ts": now, "source": "chainlink"}
        _chainlink_round_data[symbol] = {
            "roundId": str(round_id),
            "updatedAt": int(updated_at),
            "fetchTs": now,
        }
        _fallback_active[symbol] = False
        _last_error.pop(symbol, None)
        return round(price, 4)

    except Exception as e:
        err_msg = str(e)[:200]
        _last_error[symbol] = err_msg
        logger.warning(f"Chainlink: failed to fetch {symbol}: {err_msg}")
        # Reset web3 on connection errors to allow reconnect
        if "connection" in err_msg.lower() or "timeout" in err_msg.lower():
            _reset_web3()
        return None


def _mock_price(symbol: str) -> float:
    """Mock price with small random walk."""
    if symbol not in _mock_prices:
        _mock_prices[symbol] = 100.0
    p = _mock_prices[symbol]
    p *= 1 + random.uniform(-0.001, 0.001)
    _mock_prices[symbol] = p
    return round(p, 4)


def get_price(symbol: str) -> float:
    """Get price for symbol. Uses chainlink if configured, with graceful fallback."""
    try:
        if MARKET_SOURCE == "chainlink":
            price = _fetch_chainlink_price(symbol)
            if price is not None:
                _mock_prices[symbol] = price  # keep mock in sync
                return price

            # Fallback 1: last known good price
            _fallback_active[symbol] = True
            lg = _last_good.get(symbol)
            if lg:
                logger.debug(f"Chainlink fallback to last-good for {symbol} (age={int(time.time()-lg['ts'])}s)")
                return round(lg["price"], 4)

            # Fallback 2: mock price
            logger.debug(f"Chainlink fallback to mock for {symbol}")
            return _mock_price(symbol)

        return _mock_price(symbol)
    except Exception as e:
        # Ultimate safety: never crash
        logger.error(f"get_price fatal error for {symbol}: {e}")
        return _mock_price(symbol)


def get_all_prices() -> dict[str, float]:
    """Get prices for all base symbols."""
    return {s: get_price(s) for s in BASE_PRICES}


def get_strict_chainlink_price(symbol: str) -> tuple[float | None, str | None]:
    """In CHAINLINK_STRICT_ONLY mode, return (price, None) if chainlink is fresh,
    or (None, block_reason) if unavailable/stale. No fallbacks."""
    now = time.time()
    rd = _chainlink_round_data.get(symbol)
    cc = _chainlink_cache.get(symbol)

    if not rd or not rd.get("updatedAt"):
        if not cc or not cc.get("price"):
            return None, f"STRICT_CHAINLINK_BLOCKED: no chainlink data for {symbol}"
        return None, f"STRICT_CHAINLINK_BLOCKED: chainlink round data unavailable for {symbol}"

    oracle_age = now - rd["updatedAt"]
    if oracle_age > TRADING_MAX_ORACLE_AGE_SEC:
        return None, (f"STRICT_CHAINLINK_BLOCKED: oracle stale for {symbol} "
                      f"(age {int(oracle_age)}s > threshold {TRADING_MAX_ORACLE_AGE_SEC}s)")

    if not cc or not cc.get("price") or cc["price"] <= 0:
        return None, f"STRICT_CHAINLINK_BLOCKED: invalid/missing chainlink price for {symbol}"

    return round(cc["price"], 4), None


def get_effective_trading_price(symbol: str) -> tuple[float, str, str | None]:
    """Get the effective trading price with hybrid chainlink/exchange logic.

    Returns (price, source, stale_reason).
    source: "chainlink" | "live_exchange" | "last_good_fallback" | "strict_blocked"
    stale_reason: None if chainlink is fresh, else explanation string.
    """
    now = time.time()

    # === STRICT CHAINLINK ONLY MODE ===
    if CHAINLINK_STRICT_ONLY and MARKET_SOURCE == "chainlink":
        price, block_reason = get_strict_chainlink_price(symbol)
        if price is not None:
            return price, "chainlink", None
        # Return 0 price with block reason — callers must check stale_reason
        return 0.0, "strict_blocked", block_reason

    # Check if chainlink data is fresh enough for trading
    if MARKET_SOURCE == "chainlink":
        rd = _chainlink_round_data.get(symbol)
        cc = _chainlink_cache.get(symbol)

        chainlink_fresh = False
        chainlink_price = None
        stale_reason = None

        if rd and rd.get("updatedAt"):
            oracle_age = now - rd["updatedAt"]
            if oracle_age <= TRADING_MAX_ORACLE_AGE_SEC and cc and cc.get("price"):
                chainlink_fresh = True
                chainlink_price = cc["price"]
            else:
                stale_reason = f"chainlink oracle age {int(oracle_age)}s > threshold {TRADING_MAX_ORACLE_AGE_SEC}s"
        elif cc and cc.get("price"):
            # Have cached price but no round data — treat as stale
            stale_reason = "chainlink round data unavailable"
        else:
            stale_reason = "no chainlink data available"

        if chainlink_fresh and chainlink_price is not None:
            return round(chainlink_price, 4), "chainlink", None

        # Stale chainlink — try live exchange
        with _exchange_lock:
            ex = _exchange_cache.get(symbol)
        if ex and not ex.get("stale") and ex.get("price") and ex["price"] > 0:
            exchange_age = now - ex["ts"]
            if exchange_age < 120:  # exchange data < 2 min old
                return round(ex["price"], 4), "live_exchange", stale_reason

        # Fallback: last good price (never return 500 or crash)
        lg = _last_good.get(symbol)
        if lg and lg.get("price") and lg["price"] > 0:
            return round(lg["price"], 4), "last_good_fallback", stale_reason or "no live source available"

    # Mock mode or ultimate fallback
    return get_price(symbol), "mock" if MARKET_SOURCE == "mock" else "last_good_fallback", None


def get_all_effective_trading_prices() -> dict[str, dict]:
    """Get effective trading prices for all symbols. Returns {symbol: {price, source, staleReason}}."""
    result = {}
    for s in BASE_PRICES:
        price, source, stale_reason = get_effective_trading_price(s)
        result[s] = {"price": price, "source": source, "staleReason": stale_reason}
    return result


def get_market_status() -> dict:
    """Return market source health/status info with both chainlink and live exchange data."""
    now = time.time()

    # Refresh live exchange prices on every call (cheap batch call, <=3s timeout)
    try:
        _fetch_live_exchange_prices()
    except Exception as e:
        logger.warning(f"get_market_status: exchange fetch error: {e}")

    symbols_status = {}
    for symbol in BASE_PRICES:
        lg = _last_good.get(symbol)
        cc = _chainlink_cache.get(symbol)
        rd = _chainlink_round_data.get(symbol)

        # Chainlink fields
        sym_info = {
            "chainlinkPrice": round(lg["price"], 4) if lg and lg.get("source") == "chainlink" else (round(cc["price"], 4) if cc else None),
            "chainlinkRoundId": rd["roundId"] if rd else None,
            "chainlinkUpdatedAt": rd["updatedAt"] if rd else None,
            "chainlinkAgeSec": round(now - rd["updatedAt"], 1) if rd and rd.get("updatedAt") else None,
            "lastPolledAt": round(rd["fetchTs"], 3) if rd else (round(cc["ts"], 3) if cc else None),
            "pollAgeSec": round(now - rd["fetchTs"], 1) if rd else (round(now - cc["ts"], 1) if cc else None),
            "source": lg["source"] if lg else ("mock" if MARKET_SOURCE == "mock" else "none"),
            "fallbackActive": _fallback_active.get(symbol, False),
            "lastError": _last_error.get(symbol),
            # Legacy compat
            "lastPrice": lg["price"] if lg else None,
            "lastUpdate": lg["ts"] if lg else None,
            "lastUpdateAge": round(now - lg["ts"], 1) if lg else None,
        }
        if rd:
            sym_info["ageSec"] = round(now - rd["updatedAt"], 1)
            sym_info["lastFetchTs"] = round(rd["fetchTs"], 3)

        # Live exchange fields
        sym_info.update(_get_exchange_data(symbol))

        # Effective trading price
        eff_price, eff_source, eff_stale_reason = get_effective_trading_price(symbol)
        sym_info["effectiveTradingPrice"] = eff_price
        sym_info["tradingSource"] = eff_source
        sym_info["staleReason"] = eff_stale_reason

        symbols_status[symbol] = sym_info
    # Add per-symbol strict block reason
    if CHAINLINK_STRICT_ONLY and MARKET_SOURCE == "chainlink":
        for symbol in BASE_PRICES:
            _, block_reason = get_strict_chainlink_price(symbol)
            symbols_status[symbol]["strictBlocked"] = block_reason is not None
            symbols_status[symbol]["strictBlockReason"] = block_reason

    return {
        "marketSource": MARKET_SOURCE,
        "chainlinkStrictOnly": CHAINLINK_STRICT_ONLY,
        "chainlinkRpcConfigured": bool(CHAINLINK_RPC),
        "chainlinkConnected": _w3 is not None,
        "cacheTtlSec": CHAINLINK_CACHE_TTL,
        "maxStalenessSec": CHAINLINK_MAX_STALENESS,
        "tradingMaxOracleAgeSec": TRADING_MAX_ORACLE_AGE_SEC,
        "symbols": symbols_status,
    }


# ---- Quote snapshot store ----

def _cleanup_quotes():
    """Remove expired quotes. Call under _quote_lock."""
    now = time.time()
    expired = [qid for qid, q in _quote_store.items() if now - q["ts"] > QUOTE_TTL_SEC]
    for qid in expired:
        del _quote_store[qid]
    # Bound size: if still too large, remove oldest
    if len(_quote_store) > QUOTE_MAX_SIZE:
        sorted_ids = sorted(_quote_store, key=lambda k: _quote_store[k]["ts"])
        for qid in sorted_ids[:len(_quote_store) - QUOTE_MAX_SIZE]:
            del _quote_store[qid]


def issue_quote() -> dict:
    """Issue a quote snapshot with all current prices. Returns dict with quoteId, quoteTs, prices, freshness."""
    prices = get_all_prices()
    now = time.time()
    qid = uuid.uuid4().hex[:16]

    # Build per-symbol freshness
    freshness = {}
    for symbol in BASE_PRICES:
        lg = _last_good.get(symbol)
        rd = _chainlink_round_data.get(symbol)
        info: dict = {
            "source": (lg["source"] if lg else ("mock" if MARKET_SOURCE == "mock" else "none")),
        }
        if rd:
            info["chainlinkRoundId"] = rd["roundId"]
            info["chainlinkUpdatedAt"] = rd["updatedAt"]
            info["ageSec"] = round(now - rd["updatedAt"], 1)
            info["lastFetchTs"] = round(rd["fetchTs"], 3)
        freshness[symbol] = info

    # Use effective trading prices for quote snapshots
    for symbol in BASE_PRICES:
        eff_price, eff_source, eff_stale = get_effective_trading_price(symbol)
        prices[symbol] = eff_price
        freshness[symbol]["tradingSource"] = eff_source
        if eff_source == "strict_blocked":
            freshness[symbol]["strictBlocked"] = True
            freshness[symbol]["strictBlockReason"] = eff_stale

    snapshot = {"prices": prices, "ts": now, "freshness": freshness}
    with _quote_lock:
        _cleanup_quotes()
        _quote_store[qid] = snapshot

    return {"quoteId": qid, "quoteTs": now, "prices": prices, "freshness": freshness}


def resolve_quote(quote_id: str | None, symbol: str) -> tuple[float | None, str]:
    """Resolve a quote. Returns (price_or_None, execution_source).
    execution_source: "quoted" | "live_fallback" | "no_quote"
    """
    if not quote_id:
        return None, "no_quote"
    with _quote_lock:
        snap = _quote_store.get(quote_id)
    if not snap:
        return None, "live_fallback"
    if time.time() - snap["ts"] > QUOTE_TTL_SEC:
        return None, "live_fallback"
    price = snap["prices"].get(symbol)
    if price is None:
        return None, "live_fallback"
    return price, "quoted"
