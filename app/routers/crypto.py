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
from app.services.volume_profile_engine import calculate_volume_profile, is_price_near_poc, get_volume_strength

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
            stop_loss = 0.0
    take_profit = 0.0
        equity = 1.0
        peak_equity = 1.0
        max_dd = 0.0
        wins = 0
        losses = 0

        for i in range(50, len(candles)):
            window = candles[: i + 1]
            ta = ta_summary(window)
            signal = calculate_signal(window, ta)

                    # Calculate Volume Profile for lookback window (last 100 candles)
        vol_profile = calculate_volume_profile(window[-100:] if len(window) > 100 else window, num_bins=20)
        poc = vol_profile.get("poc", 0)
        vah = vol_profile.get("vah", 0)
        val = vol_profile.get("val", 0)
        
        # Get VWAP from TA
        vwap_dict = ta.get("vwap", {})
        vwap_daily = float(vwap_dict.get("daily", 0)) if isinstance(vwap_dict, dict) else 0.0
        
        # Calculate average volume for volume strength
        recent_volumes = [float(c.volume) if hasattr(c, 'volume') else float(c.get('volume', 0)) for c in window[-20:]]        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 1
        current_volume = float(window[-1].volume) if hasattr(window[-1], 'volume') else float(window[-1].get('volume', 0))
        volume_strength = get_volume_strength(current_volume, avg_volume)

            price = float(window[-1].close)
        atr = float(ta.get("atr", 0))
            rsi = float(ta.get("rsi", 50))
            direction = str(signal.get("direction", "neutral")).lower()

            # exit logic
        if position == 1 and (direction == "bearish" or rsi > 70 or (stop_loss > 0 and price <= stop_loss) or (take_profit > 0 and price >= take_profit)):                ret = (price - entry_price) / entry_price
                equity *= (1 + ret)
                if ret > 0:
                    wins += 1
                else:
                    losses += 1
                position = 0
                entry_price = 0.0
            stop_loss = 0.0
            take_profit = 0.0

            # entry logic
            # entry logic with Volume Profile filters
            in_value_area = (val <= price <= vah) if (val and vah) else True
            near_poc = is_price_near_poc(price, poc, threshold_pct=0.02) if poc else True
            strong_volume = volume_strength in ('high', 'normal')
            above_vwap = price > vwap_daily if vwap_daily > 0 else True
            
            if position == 0 and direction == "bullish" and rsi < 60 and in_value_area and near_poc and above_vwap and strong_volume:                position = 1
                entry_price = price
            # Set ATR-based stop-loss and take-profit
            stop_loss = price - (2 * atr)  # 2x ATR below entry
            take_profit = price + (3 * atr)  # 3x ATR above entry (1.5:1 R:R)

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
