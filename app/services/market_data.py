import random

BASE_PRICES = {
    "BTCUSDT": 67000.0,
    "ETHUSDT": 3500.0,
    "SOLUSDT": 145.0,
}

_current: dict[str, float] = dict(BASE_PRICES)


def get_price(symbol: str) -> float:
    if symbol not in _current:
        _current[symbol] = 100.0
    p = _current[symbol]
    p *= 1 + random.uniform(-0.001, 0.001)
    _current[symbol] = p
    return round(p, 4)


def get_all_prices() -> dict[str, float]:
    return {s: get_price(s) for s in BASE_PRICES}
