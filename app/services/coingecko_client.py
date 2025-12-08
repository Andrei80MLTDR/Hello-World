import httpx
from app.config import COINGECKO_API_KEY

COINGECKO_BASE_URL = "https://pro-api.coingecko.com/api/v3"

async def get_coingecko_price(coin_id: str = "bitcoin", vs_currency: str = "usd") -> float:
    url = f"{COINGECKO_BASE_URL}/simple/price"
    headers = {"x-cg-pro-api-key": COINGECKO_API_KEY} if COINGECKO_API_KEY else {}
    params = {"ids": coin_id, "vs_currencies": vs_currency}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # {"bitcoin": {"usd": 67187.33, ...}}
        return float(data[coin_id][vs_currency])
