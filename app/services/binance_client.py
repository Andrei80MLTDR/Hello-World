import httpx

BINANCE_BASE_URL = "https://api.binance.com"

async def get_binance_price(symbol: str) -> float:
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/price"
    params = {"symbol": symbol}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        # Binance returns {"symbol": "BTCUSDT", "price": "12345.6789"}
        return float(data["price"])
