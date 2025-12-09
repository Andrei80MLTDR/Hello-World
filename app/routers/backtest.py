from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List
import numpy as np

from app.services.binance_service import BinanceService
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal
from app.services.backtest_metrics import calculate_metrics

router = APIRouter(prefix="/backtest", tags=["backtest"])
binance_service = BinanceService()


def run_backtest(candles, rsi_buy: float = 60.0, rsi_sell: float = 70.0, min_window: int = 50):
    """Execută backtest pe candles"""
    if len(candles) < min_window:
        return [], [1.0]
    
    trades = []
    equity_curve = [1.0]
    position = 0
    entry_price = 0.0
    
    for i in range(min_window, len(candles)):
        window = candles[:i+1]
        ta = ta_summary(window)
        signal = calculate_signal(window, ta)
        
        current_price = float(candles[i].close)
        rsi = ta.get("rsi", 50.0)
        direction = str(signal.get("direction", "neutral")).lower()
        
        # EXIT
        if position == 1:
            if direction == "bearish" or rsi > rsi_sell:
                pnl = (current_price - entry_price) / entry_price
                trades.append(pnl)
                equity_curve.append(equity_curve[-1] * (1 + pnl))
                position = 0
        
        # ENTRY
        if position == 0:
            if direction == "bullish" and rsi < rsi_buy:
                position = 1
                entry_price = current_price
    
    # Close position dacă rămâne deschis
    if position == 1:
        final_pnl = (float(candles[-1].close) - entry_price) / entry_price
        trades.append(final_pnl)
        equity_curve.append(equity_curve[-1] * (1 + final_pnl))
    
    return trades, equity_curve


# ==================== ENDPOINT 1: Single Timeframe ====================
@router.get("/single-tf")
async def backtest_single_tf(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(1000, ge=100, le=5000),
    rsi_buy: float = Query(60.0, ge=0, le=100),
    rsi_sell: float = Query(70.0, ge=0, le=100),
):
    """Backtest pe un timeframe cu parametri customizabili
    
    Example: /backtest/single-tf?symbol=BTCUSDT&interval=4h&limit=1000&rsi_buy=55&rsi_sell=75
    """
    try:
        candles = binance_service.get_candles(symbol, interval, limit)
        if len(candles) < 50:
            raise HTTPException(status_code=400, detail=f"Need 50+ candles, got {len(candles)}")
        
        trades, equity_curve = run_backtest(candles, rsi_buy, rsi_sell)
        metrics = calculate_metrics(trades, equity_curve)
        
        return {
            "symbol": symbol,
            "interval": interval,
            "candles_used": len(candles),
            "parameters": {"rsi_buy": rsi_buy, "rsi_sell": rsi_sell},
            "metrics": metrics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 2: Multi Timeframe ====================
@router.get("/multi-tf")
async def backtest_multi_tf(
    symbol: str = Query("BTCUSDT"),
    limit: int = Query(1000, ge=100, le=5000),
    rsi_buy: float = Query(60.0),
    rsi_sell: float = Query(70.0),
):
    """Backtest pe 1h, 4h, 1d - compară timeframe-uri
    
    Example: /backtest/multi-tf?symbol=BTCUSDT&limit=1000
    """
    timeframes = ["1h", "4h", "1d"]
    results = {}
    
    try:
        for tf in timeframes:
            candles = binance_service.get_candles(symbol, tf, limit)
            if len(candles) < 50:
                results[tf] = {"error": f"Insufficient candles: {len(candles)}"}
                continue
            
            trades, equity_curve = run_backtest(candles, rsi_buy, rsi_sell)
            metrics = calculate_metrics(trades, equity_curve)
            results[tf] = metrics
        
        # Find best
        best_tf = max(
            [(k, v) for k, v in results.items() if "error" not in v],
            key=lambda x: x[1].get("profit_factor", 0),
            default=(None, {})
        )
        
        return {
            "symbol": symbol,
            "limit": limit,
            "timeframes": results,
            "best_timeframe": best_tf[0],
            "best_metrics": best_tf[1] if best_tf[0] else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 3: Batch Multiple Symbols ====================
@router.get("/batch")
async def backtest_batch(
    symbols: str = Query("BTCUSDT,ETHUSDT"),
    timeframes: str = Query("4h,1d"),
    limit: int = Query(1000, ge=100, le=5000),
    rsi_buy: float = Query(60.0),
    rsi_sell: float = Query(70.0),
):
    """Backtest pe multiple simboluri și timeframe-uri
    
    Example: /backtest/batch?symbols=BTCUSDT,ETHUSDT,XRPUSDT&timeframes=4h,1d&limit=1000
    """
    symbols_list = [s.strip().upper() for s in symbols.split(",")]
    timeframes_list = [t.strip() for t in timeframes.split(",")]
    
    batch_results = {}
    
    try:
        for symbol in symbols_list:
            batch_results[symbol] = {}
            
            for tf in timeframes_list:
                try:
                    candles = binance_service.get_candles(symbol, tf, limit)
                    if len(candles) < 50:
                        batch_results[symbol][tf] = {"error": "Insufficient candles"}
                        continue
                    
                    trades, equity_curve = run_backtest(candles, rsi_buy, rsi_sell)
                    metrics = calculate_metrics(trades, equity_curve)
                    batch_results[symbol][tf] = metrics
                except Exception as e:
                    batch_results[symbol][tf] = {"error": str(e)}
        
        # Summary
        summary = {}
        for symbol in symbols_list:
            best_pf = 0
            best_tf = None
            for tf, data in batch_results[symbol].items():
                if "error" not in data:
                    pf = data.get("profit_factor", 0)
                    if pf > best_pf:
                        best_pf = pf
                        best_tf = tf
            summary[symbol] = {"best_tf": best_tf, "best_profit_factor": round(best_pf, 2)}
        
        return {
            "symbols": symbols_list,
            "timeframes": timeframes_list,
            "limit": limit,
            "results": batch_results,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 4: Parameter Optimization ====================
@router.get("/optimize")
async def backtest_optimize(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(1000, ge=100, le=5000),
):
    """Testează multiple RSI parameters și returnează best combination
    
    Testează: RSI_buy: 30-65, RSI_sell: 65-80
    Example: /backtest/optimize?symbol=BTCUSDT&interval=4h&limit=1000
    """
    results = {}
    
    try:
        candles = binance_service.get_candles(symbol, interval, limit)
        if len(candles) < 50:
            raise HTTPException(status_code=400, detail="Insufficient candles")
        
        # Test toate combinațiile
        for rsi_buy in range(30, 70, 5):
            for rsi_sell in range(65, 85, 5):
                if rsi_sell <= rsi_buy:
                    continue
                
                trades, equity_curve = run_backtest(candles, rsi_buy, rsi_sell)
                metrics = calculate_metrics(trades, equity_curve)
                
                key = f"buy_{rsi_buy}_sell_{rsi_sell}"
                results[key] = metrics
        
        # Find best
        best = max(results.items(), key=lambda x: x[1].get("profit_factor", 0))
        best_key = best[0]
        best_metrics = best[1]
        
        # Parse best params
        best_buy = int(best_key.split("_")[1])
        best_sell = int(best_key.split("_")[3])
        
        return {
            "symbol": symbol,
            "interval": interval,
            "candles_used": len(candles),
            "best_parameters": {
                "rsi_buy": best_buy,
                "rsi_sell": best_sell,
                "profit_factor": round(best_metrics.get("profit_factor", 0), 2),
                "win_rate_pct": best_metrics.get("win_rate_pct", 0),
                "total_return_pct": best_metrics.get("total_return_pct", 0),
            },
            "all_results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 5: Quick Stats ====================
@router.get("/stats")
async def backtest_quick_stats(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(500, ge=50, le=2000),
):
    """Return quick stats fără backtest - doar indicatori pe latest candles
    
    Example: /backtest/stats?symbol=BTCUSDT&interval=4h
    """
    try:
        candles = binance_service.get_candles(symbol, interval, limit)
        if len(candles) < 20:
            raise HTTPException(status_code=400, detail="Insufficient candles")
        
        # Lucrează cu ultimele 100 candles
        ta = ta_summary(candles[-100:])
        signal = calculate_signal(candles[-100:], ta)
        
        return {
            "symbol": symbol,
            "interval": interval,
            "current_candle": {
                "open": float(candles[-1].open),
                "high": float(candles[-1].high),
                "low": float(candles[-1].low),
                "close": float(candles[-1].close),
            },
            "indicators": {
                "ema_fast": round(ta.get("ema_fast", 0), 2),
                "ema_slow": round(ta.get("ema_slow", 0), 2),
                "rsi": round(ta.get("rsi", 0), 2),
                "macd": round(ta.get("macd", 0), 4),
                "signal_line": round(ta.get("signal_line", 0), 4),
            },
            "signal": signal,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
