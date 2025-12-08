from fastapi import APIRouter
from typing import List
from app.models.dto import NewsItem

router = APIRouter(prefix="/news", tags=["news"])

@router.get("/", response_model=List[NewsItem])
async def get_news():
    return []
