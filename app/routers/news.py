from fastapi import APIRouter, HTTPException
from typing import List
from app.models.dto import NewsItem
from app.services.newsdata_client import get_crypto_news

router = APIRouter(prefix="/news", tags=["news"])

@router.get("/", response_model=List[NewsItem])
async def get_news(limit: int = 20):
    try:
        items = await get_crypto_news(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News API error: {e}")
    return [NewsItem(**item) for item in items]
