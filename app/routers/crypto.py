from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.models.dto import PriceResponse, Candle, TASummary
from app.services.binance_client import get_binance_price
from app.services.binance_ohlc import get_klines
from app.services.ta_engine import ta_summary

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


@router.get("/ta-summary", response_model=TASummary)
async def get_ta_summary(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 150,
):
    try:
        candles = await get_klines(symbol=symbol, interval=interval, limit=limit)
        summary = ta_summary(candles)
        return TASummary(**summary)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TA analysis error: {e}")
