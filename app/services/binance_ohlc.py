import httpx
from typing import List, Literal

BINANCE_BASE_URL = "https://api.binance.com"

IntervalType = Literal["1m", "5m", "15m", "1h", "4h", "1d"]

async def get_klines(
    symbol: str,
    interval: IntervalType = "1h",
    limit: int = 100,
) -> List[dict]:
    """
    Returnează lista de lumânări ca dict-uri simple:
    [
      {"open_time": 123, "open": 1.0, "high": 2.0, "low": 0.9, "close": 1.5, "volume": 123.4},
      ...
    ]
    """
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()

    candles: List[dict] = []
    for item in raw:
        candles.append(
            {
                "open_time": item[0],
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
            }
        )
    return candles
