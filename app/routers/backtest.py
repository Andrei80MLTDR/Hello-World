from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List, Optional
import numpy as np

from app.services.binance_service import BinanceService
from app.services.klines_cache import get_or_cache_klines
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal
from app.services.backtest_metrics import calculate_metrics, compare_timeframes

router = APIRouter(prefix="/backtest", tags=["backtest"])
binance_service = BinanceService()


def run_backtest_simple(
    candles,
    rsi_buy_threshold: float = 60.0,
    rsi_sell_threshold: float = 70.0,
    min_window: int = 50,
) -> tuple[List[float], List[float]]:
    """
    Execută backtest simplu pe o serie de candles.
    
    Returns:
        (trades, equity_curve) - lista de PnL și evolution equity
    """
    if len(candles) < min_window:
        return [], [1.0]
    
    trades = []
    equity_curve = [1.0]
    position = 0
    entry_price = 0.0
    
    for i in range(min_window, len(candles)):
        # Lucrează cu fereastra până la candle curent
        window = candles[:i+1]
        
        # Calculează indicatori
        ta = ta_summary(window)
        signal = calculate_signal(window, ta)
        
        current_price = float(candles[i].close)
        rsi = ta.get("rsi", 50.0)
        direction = signal.get("direction", "neutral").lower()
        
        # === EXIT LOGIC ===
        if position == 1:  # In a long position
            should_exit = (
                direction == "bearish" or 
                rsi > rsi_sell_threshold
            )
            if should_exit:
                pnl = (current_price - entry_price) / entry_price
                trades.append(pnl)
                equity_curve.append(equity_curve[-1] * (1 + pnl))
                position = 0
                entry_price = 0.0
        
        # === ENTRY LOGIC ===
        if position == 0:  # Not in position
            should_enter = (
                direction == "bullish" and 
                rsi < rsi_buy_threshold
            )
            if should_enter:
                position = 1
                entry_price = current_price
    
    # Close position dacă rămâne deschis
    if position == 1:
        final_pnl = (float(candles[-1].close) - entry_price) / entry_price
        trades.append(final_pnl)
        equity_curve.append(equity_curve[-1] * (1 + final_pnl))
    
    return trades, equity_curve


# ============================================================
# ENDPOINT 1: Single Timeframe Backtest
# ============================================================
@router.get("/single-tf")
async def backtest_single_timeframe(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(1000, ge=100, le=5000),
    rsi_buy: float = Query(60.0, ge=0, le=100),
    rsi_sell: float = Query(70.0, ge=0, le=100),
):
    """
    Backtest pe un singur timeframe cu parametri customizabili.
    
    Example:
        GET /backtest/single-tf?symbol=BTCUSDT&interval=4h&limit=1000&rsi_buy=55&rsi_sell=75
    """
    try:
        candles = binance_service.get_candles(symbol, interval, limit)
        if len(candles) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient candles: {len(candles)}, need at least 50"
            )
        
        trades, equity_curve = run_backtest_simple(
            candles,
            rsi_buy_threshold=rsi_buy,
            rsi_sell_threshold=rsi_sell,
        )
        
        metrics = calculate_metrics(trades, equity_curve)
        
        return {
            "symbol": symbol,
            "interval": interval,
            "candles_used": len(candles),
            "parameters": {
                "rsi_buy_threshold": rsi_buy,
                "rsi_sell_threshold": rsi_sell,
            },
            "metrics": metrics,
            "equity_curve_sample": {
                "start": equity_curve[0],
                "end": equity_curve[-1],
                "datapoints": len(equity_curve),
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ENDPOINT 2: Multi-Timeframe Backtest
# ============================================================
@router.get("/multi-tf")
async def backtest_multi_timeframe(
    symbol: str = Query("BTCUSDT"),
    limit: int = Query(1000, ge=100, le=5000),
    rsi_buy: float = Query(60.0),
    rsi_sell: float = Query(70.0),
):
    """
    Backtest pe multiple timeframe-uri (1h, 4h, 1d).
    
    Example:
        GET /backtest/multi-tf?symbol
