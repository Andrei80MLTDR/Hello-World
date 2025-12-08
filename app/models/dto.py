from pydantic import BaseModel
from typing import Optional, List

class PriceResponse(BaseModel):
    symbol: str
    price: float

class NewsItem(BaseModel):
    title: str
    source: str
    url: str
    published_at: str

class EconEvent(BaseModel):
    country: str
    event: str
    impact: str
    time: str
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    
class Candle(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
