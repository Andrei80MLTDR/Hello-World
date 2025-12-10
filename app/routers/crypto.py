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
from app.services.ta_engine import ta_summary, get_ohlcv
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
    candles = get_ohlcv(symbol=symbol, interval=interval, limit=limit)
            if len(candles) < 100:            raise HTTPException(status_code=400, detail="Not enough candles for backtest")

        position = 0  # 0=flat, 1=long, -1=short
        entry_price = 0.0
        stop_loss = 0.0
        take_profit = 0.0
        equity = 1.0
        peak_equity = 1.0
        max_dd = 0.0
        wins = 0
        losses = 0
        long_trades = 0
        short_trades = 0

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
            recent_volumes = [float(c.volume) if hasattr(c, 'volume') else float(c.get('volume', 0)) for c in window[-20:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 1
            current_volume = float(window[-1].volume) if hasattr(window[-1], 'volume') else float(window[-1].get('volume', 0))
            volume_strength = get_volume_strength(current_volume, avg_volume)

            price = float(window[-1].close)
            atr = float(ta.get("atr", 0))
            rsi = float(ta.get("rsi", 50))
            ema_slow = float(ta.get("ema_slow", 0))
            
            # Extract MACD
            macd_dict = ta.get("macd", {})
            macd_value = float(macd_dict.get("macd", 0))
            macd_signal = float(macd_dict.get("signal", 0))

            # Volume Profile conditions
            in_value_area = (val <= price <= vah) if (val and vah) else True
            near_poc = is_price_near_poc(price, poc, threshold_pct=0.02) if poc else True
            strong_volume = volume_strength in ('high', 'normal')
            above_vwap = price > vwap_daily if vwap_daily > 0 else False
            below_vwap = price < vwap_daily if vwap_daily > 0 else False

            # ==== HYPOTHESIS A - LONG CONDITIONS ====
            long_cond1_trend = price > ema_slow and ema_slow > 0  # Uptrend
            long_cond2_momentum = (macd_value > macd_signal) and (40 < rsi < 70)  # Bullish momentum, not overbought
            long_cond3_vol_profile = in_value_area and near_poc and above_vwap  # Institutional support
            long_cond4_volume = strong_volume  # Active participation

            # ==== HYPOTHESIS B - SHORT CONDITIONS ====
            short_cond1_trend = price < ema_slow and ema_slow > 0  # Downtrend
            short_cond2_momentum = (macd_value < macd_signal) and (30 < rsi < 60)  # Bearish momentum, not oversold
            short_cond3_vol_profile = in_value_area and near_poc and below_vwap  # Institutional resistance
            short_cond4_volume = strong_volume  # Active participation

            # Trailing stop-loss logic for LONG positions
            if position == 1 and stop_loss > 0:
                profit = price - entry_price
                # Move stop to breakeven when profit >= 1x ATR
                if profit >= atr and stop_loss < entry_price:
                    stop_loss = entry_price
                # Trail stop by 0.5x ATR as price moves up
                elif profit > atr:
                    potential_stop = price - (0.5 * atr)
                    if potential_stop > stop_loss:
                        stop_loss = potential_stop

            # Trailing stop-loss logic for SHORT positions
            if position == -1 and stop_loss > 0:
                profit = entry_price - price
                # Move stop to breakeven when profit >= 1x ATR
                if profit >= atr and stop_loss > entry_price:
                    stop_loss = entry_price
                # Trail stop by 0.5x ATR as price moves down
                elif profit > atr:
                    potential_stop = price + (0.5 * atr)
                    if potential_stop < stop_loss:
                        stop_loss = potential_stop

            # ==== EXIT LOGIC FOR LONG ====
            if position == 1 and (
                (stop_loss > 0 and price <= stop_loss) or 
                (take_profit > 0 and price >= take_profit) or
                short_cond2_momentum  # Exit on bearish momentum reversal
            ):
                ret = (price - entry_price) / entry_price
                equity *= (1 + ret)
                if ret > 0:
                    wins += 1
                else:
                    losses += 1
                position = 0
                entry_price = 0.0
                stop_loss = 0.0
                take_profit = 0.0

            # ==== EXIT LOGIC FOR SHORT ====
            elif position == -1 and (
                (stop_loss > 0 and price >= stop_loss) or 
                (take_profit > 0 and price <= take_profit) or
                long_cond2_momentum  # Exit on bullish momentum reversal
            ):
                ret = (entry_price - price) / entry_price  # Inverted for shorts
                equity *= (1 + ret)
                if ret > 0:
                    wins += 1
                else:
                    losses += 1
                position = 0
                entry_price = 0.0
                stop_loss = 0.0
                take_profit = 0.0

            # ==== ENTRY LOGIC - LONG (Hypothesis A) ====
            if position == 0 and all([long_cond1_trend, long_cond2_momentum, long_cond3_vol_profile, long_cond4_volume]):
                position = 1
                entry_price = price
                stop_loss = entry_price - (1 * atr)  # 1x ATR stop
                take_profit = entry_price + (3 * atr)  # 3x ATR target (1:3 R:R)
                long_trades += 1

            # ==== ENTRY LOGIC - SHORT (Hypothesis B) ====
            elif position == 0 and all([short_cond1_trend, short_cond2_momentum, short_cond3_vol_profile, short_cond4_volume]):
                position = -1
                entry_price = price
                stop_loss = entry_price + (1 * atr)  # 1x ATR stop
                take_profit = entry_price - (3 * atr)  # 3x ATR target (1:3 R:R)
                short_trades += 1

            # Track drawdown
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
            "long_trades": long_trades,
            "short_trades": short_trades,
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
