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

@router.get("/klines")
async def get_klines(symbol: str, interval: str):
    return await BinanceService.get_klines(symbol=symbol, interval=interval)

from fastapi import APIRouter, Query, HTTPException
from app.services.binance_service import BinanceService
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal

router = APIRouter(prefix="/crypto", tags=["crypto"])

binance_service = BinanceService()

@router.get("/backtest")
async def backtest_simple(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(1000, ge=100, le=2000),
):
    try:
        candles = binance_service.get_candles(symbol=symbol, interval=interval, limit=limit)
        if len(candles) < 100:
            raise HTTPException(status_code=400, detail="Not enough candles for backtest")

        position = 0
        entry_price = 0.0
        equity = 1.0
        peak_equity = 1.0
        max_dd = 0.0
        wins = 0
        losses = 0

        for i in range(50, len(candles)):
            window = candles[: i + 1]
            ta = ta_summary(window)
            signal = calculate_signal(window, ta)

            price = float(window[-1].close)
            rsi = float(ta.get("rsi", 50))
            direction = str(signal.get("direction", "neutral")).lower()

            # exit logic
            if position == 1 and (direction == "bearish" or rsi > 70):
                ret = (price - entry_price) / entry_price
                equity *= (1 + ret)
                if ret > 0:
                    wins += 1
                else:
                    losses += 1
                position = 0
                entry_price = 0.0

            # entry logic
            if position == 0 and direction == "bullish" and rsi < 60:
                position = 1
                entry_price = price

            # track drawdown
            if equity > peak_equity:
                peak_equity = equity
            dd = (peak_equity - equity) / peak_equity
            if dd > max_dd:
                max_dd = dd

        trades = wins + losses
        return {
            "symbol": symbol,
            "interval": interval,
            "candles_used": len(candles),
            "trades": trades,
            "wins": wins,
            "losses": losses,
            "win_rate_pct": (wins / trades * 100) if trades else 0.0,
            "final_equity": equity,
            "total_return_pct": (equity - 1) * 100,
            "max_drawdown_pct": max_dd * 100,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
