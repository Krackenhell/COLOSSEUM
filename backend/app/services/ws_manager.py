"""WebSocket price feed manager for ws_mvp mode.

Connects to OKX (primary) and Coinbase (secondary) public WebSocket tickers.
Maintains in-memory latest prices with staleness detection and auto-reconnect.
"""
import json
import time
import threading
import logging
import ssl

logger = logging.getLogger(__name__)

# --- Config ---
WS_STALE_THRESHOLD_SEC = 15  # >15s no update = stale
WS_RECONNECT_BASE_SEC = 2
WS_RECONNECT_MAX_SEC = 60

# Symbol mapping
SYMBOLS = ["BTCUSDT", "ETHUSDT", "AVAXUSDT"]

OKX_WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
OKX_SYMBOL_MAP = {
    "BTCUSDT": "BTC-USDT",
    "ETHUSDT": "ETH-USDT",
    "AVAXUSDT": "AVAX-USDT",
}

COINBASE_WS_URL = "wss://ws-feed.exchange.coinbase.com"
COINBASE_SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "AVAXUSDT": "AVAX-USD",
}

# --- State ---
_lock = threading.Lock()
_prices: dict[str, dict] = {}  # symbol -> {"price": float, "ts": float, "source": str}
_provider_status: dict[str, dict] = {}  # provider -> {"connected": bool, "lastMsg": float, "error": str|None, "reconnects": int}
_started = False
_threads: list[threading.Thread] = []


def _init_provider_status():
    for p in ("okx", "coinbase"):
        if p not in _provider_status:
            _provider_status[p] = {"connected": False, "lastMsg": 0, "error": None, "reconnects": 0}


def get_ws_price(symbol: str) -> dict | None:
    """Get WS price for symbol. Returns dict with price/ts/source/ageSec/stale or None."""
    with _lock:
        entry = _prices.get(symbol)
    if not entry:
        return None
    now = time.time()
    age = now - entry["ts"]
    return {
        "price": entry["price"],
        "ts": entry["ts"],
        "source": entry["source"],
        "ageSec": round(age, 1),
        "stale": age > WS_STALE_THRESHOLD_SEC,
    }


def get_ws_status() -> dict:
    """Overall WS status for market-status endpoint."""
    with _lock:
        providers = {}
        for name, st in _provider_status.items():
            now = time.time()
            providers[name] = {
                "connected": st["connected"],
                "lastMsgAgeSec": round(now - st["lastMsg"], 1) if st["lastMsg"] > 0 else None,
                "error": st["error"],
                "reconnects": st["reconnects"],
            }
        prices = {}
        for sym in SYMBOLS:
            entry = _prices.get(sym)
            if entry:
                age = time.time() - entry["ts"]
                prices[sym] = {
                    "wsPrice": round(entry["price"], 4),
                    "wsTs": round(entry["ts"], 3),
                    "wsAgeSec": round(age, 1),
                    "wsSource": entry["source"],
                    "wsStale": age > WS_STALE_THRESHOLD_SEC,
                }
            else:
                prices[sym] = {"wsPrice": None, "wsTs": None, "wsAgeSec": None, "wsSource": None, "wsStale": True}
    any_connected = any(p["connected"] for p in providers.values())
    return {"wsConnected": any_connected, "wsProviders": providers, "wsPrices": prices}


def _update_price(symbol: str, price: float, source: str):
    """Thread-safe price update."""
    if price <= 0:
        return
    now = time.time()
    with _lock:
        existing = _prices.get(symbol)
        # Accept if no existing or newer or from higher-priority source
        if not existing or now - existing["ts"] > 0.05:
            _prices[symbol] = {"price": price, "ts": now, "source": source}
        _provider_status.setdefault(source, {})["lastMsg"] = now


def _run_okx():
    """OKX WebSocket connection loop with reconnect."""
    import websocket
    backoff = WS_RECONNECT_BASE_SEC

    while _started:
        try:
            with _lock:
                _provider_status["okx"]["connected"] = False
                _provider_status["okx"]["error"] = None

            ws = websocket.create_connection(
                OKX_WS_URL,
                timeout=30,
                sslopt={"cert_reqs": ssl.CERT_NONE},
            )

            # Subscribe to tickers
            args = [{"channel": "tickers", "instId": inst} for inst in OKX_SYMBOL_MAP.values()]
            ws.send(json.dumps({"op": "subscribe", "args": args}))

            with _lock:
                _provider_status["okx"]["connected"] = True
            logger.info("OKX WS connected")
            backoff = WS_RECONNECT_BASE_SEC

            while _started:
                try:
                    raw = ws.recv()
                    if not raw:
                        continue
                    msg = json.loads(raw)

                    # Ticker data
                    if "data" in msg and "arg" in msg:
                        for tick in msg["data"]:
                            inst_id = tick.get("instId", "")
                            last = tick.get("last")
                            if last:
                                price = float(last)
                                # Reverse map
                                for our_sym, okx_sym in OKX_SYMBOL_MAP.items():
                                    if okx_sym == inst_id:
                                        _update_price(our_sym, price, "okx")
                                        break
                except Exception as e:
                    if not _started:
                        break
                    logger.warning(f"OKX WS recv error: {e}")
                    break

            try:
                ws.close()
            except Exception:
                pass

        except Exception as e:
            with _lock:
                _provider_status["okx"]["connected"] = False
                _provider_status["okx"]["error"] = str(e)[:200]
                _provider_status["okx"]["reconnects"] += 1
            logger.warning(f"OKX WS connect error: {e}, reconnect in {backoff}s")

        if _started:
            time.sleep(backoff)
            backoff = min(backoff * 2, WS_RECONNECT_MAX_SEC)


def _run_coinbase():
    """Coinbase WebSocket connection loop with reconnect."""
    import websocket
    backoff = WS_RECONNECT_BASE_SEC

    while _started:
        try:
            with _lock:
                _provider_status["coinbase"]["connected"] = False
                _provider_status["coinbase"]["error"] = None

            ws = websocket.create_connection(
                COINBASE_WS_URL,
                timeout=30,
                sslopt={"cert_reqs": ssl.CERT_NONE},
            )

            product_ids = list(COINBASE_SYMBOL_MAP.values())
            ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": product_ids,
                "channels": ["ticker"],
            }))

            with _lock:
                _provider_status["coinbase"]["connected"] = True
            logger.info("Coinbase WS connected")
            backoff = WS_RECONNECT_BASE_SEC

            while _started:
                try:
                    raw = ws.recv()
                    if not raw:
                        continue
                    msg = json.loads(raw)

                    if msg.get("type") == "ticker":
                        product_id = msg.get("product_id", "")
                        price_str = msg.get("price")
                        if price_str:
                            price = float(price_str)
                            for our_sym, cb_sym in COINBASE_SYMBOL_MAP.items():
                                if cb_sym == product_id:
                                    _update_price(our_sym, price, "coinbase")
                                    break
                except Exception as e:
                    if not _started:
                        break
                    logger.warning(f"Coinbase WS recv error: {e}")
                    break

            try:
                ws.close()
            except Exception:
                pass

        except Exception as e:
            with _lock:
                _provider_status["coinbase"]["connected"] = False
                _provider_status["coinbase"]["error"] = str(e)[:200]
                _provider_status["coinbase"]["reconnects"] += 1
            logger.warning(f"Coinbase WS connect error: {e}, reconnect in {backoff}s")

        if _started:
            time.sleep(backoff)
            backoff = min(backoff * 2, WS_RECONNECT_MAX_SEC)


def start():
    """Start WS manager threads. Safe to call multiple times (idempotent)."""
    global _started
    if _started:
        return
    _started = True
    _init_provider_status()
    for fn, name in [(_run_okx, "ws-okx"), (_run_coinbase, "ws-coinbase")]:
        t = threading.Thread(target=fn, name=name, daemon=True)
        t.start()
        _threads.append(t)
    logger.info("WS price manager started (OKX + Coinbase)")


def stop():
    """Stop WS manager. Threads will exit on next iteration."""
    global _started
    _started = False
    logger.info("WS price manager stopping")
