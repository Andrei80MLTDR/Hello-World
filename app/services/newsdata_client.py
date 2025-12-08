import httpx
from typing import List
from app.config import NEWSDATA_API_KEY

BASE_URL = "https://newsdata.io/api/1/news"

async def get_crypto_news(limit: int = 20) -> List[dict]:
    """
    Returnează ultimele știri generale (nu doar crypto) pentru test.
    Dacă nu există cheie, întoarce listă goală.
    """
    if not NEWSDATA_API_KEY:
        return []

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": "bitcoin OR crypto OR ethereum OR stocks",
        "language": "en",
        "page": 1,
        "size": limit,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results") or []
    cleaned: List[dict] = []
    for item in results:
        cleaned.append(
            {
                "title": item.get("title") or "",
                "source": item.get("source_id") or "",
                "url": item.get("link") or "",
                "published_at": item.get("pubDate") or "",
            }
        )
    return cleaned
