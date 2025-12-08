from fastapi import APIRouter, HTTPException
from typing import List
from app.models.dto import PriceResponse, Candle
from app.services.binance_client import get_binance_price
from app.services.binance_ohlc import get_klines

router = APIRouter(prefix="/crypto", tags=["crypto"])

@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str = "BTCUSDT"):
    try:
        price = await get_binance_price(symbol)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Binance price error: {e}")
    return PriceResponse(symbol=symbol, price=price)

@router.get("/ohlc", response_model=List[Candle])
async def get_ohlc(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100,
):
    try:
        candles = await get_klines(symbol=symbol, interval=interval, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Binance klines error: {e}")
    return candles
