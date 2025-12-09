from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List, Optional
import numpy as np
import time
import logging
from app.services.binance_service import BinanceService
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal
from app.services.backtest_metrics import calculate_metrics
from app.services.advanced_statistical_engine import AdvancedStatisticalEngine, StatisticalMetrics

router = APIRouter(prefix="/backtest", tags=["backtest"])
binance_service = BinanceService()

logger = logging.getLogger(__name__)
statistical_engine = AdvancedStatisticalEngine(initial_capital=10000.0)

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
            if final_pnl not in trades:
                trades.append(final_pnl)
                equity_curve.append(equity_curve[-1] * (1 + final_pnl))
    
    return trades, equity_curve

# ==================== ENDPOINT 6: LARGE-SCALE BACKTEST ====================
@router.get("/large-scale")
async def backtest_large_scale(
    symbols: str = Query("BTCUSDT,ETHUSDT,XRPUSDT"),
    timeframes: str = Query("4h,1d"),
    limit: int = Query(2000, ge=500, le=5000),
    rsi_buy: float = Query(45.0, ge=20, le=80),
    rsi_sell: float = Query(65.0, ge=20, le=80),
):
    """
    Large-scale backtesting across MULTIPLE symbols and timeframes.
    Test system limits and performance at scale.
    
    Parameters:
    - symbols: CSV list (BTCUSDT,ETHUSDT,XRPUSDT,ADAUSDT,DOGEUSDT)
    - timeframes: CSV list (1h,4h,1d,1w)
    - limit: 500-5000 candles per symbol/timeframe
    - rsi_buy: Entry signal (lower = more aggressive)
    - rsi_sell: Exit signal (higher = more aggressive)
    
    Example:
    /backtest/large-scale?symbols=BTCUSDT,ETHUSDT,XRPUSDT&timeframes=4h,1d&limit=2000&rsi_buy=50&rsi_sell=70
    """
    start_time = time.time()
    symbols_list = [s.strip().upper() for s in symbols.split(",")]
    timeframes_list = [t.strip() for t in timeframes.split(",")]
    
    results = {}
    summary = {"total_tests": 0, "successful": 0, "failed": 0, "best_performers": []}
    
    try:
        for symbol in symbols_list:
            results[symbol] = {}
            
            for tf in timeframes_list:
                try:
                    candles = binance_service.get_candles(symbol, tf, limit)
                    
                    if len(candles) < 50:
                        results[symbol][tf] = {"error": f"Insufficient candles: {len(candles)}"}
                        summary["failed"] += 1
                        summary["total_tests"] += 1
                        continue
                    
                    trades, equity_curve = run_backtest(candles, rsi_buy, rsi_sell)
                    95
                    (trades, equity_curve)
                                        
                    # Calculate advanced statistical metrics
                    try:
                        win_rate = metrics.get('win_rate_pct', 0) / 100 if metrics.get('win_rate_pct', 0) > 0 else 0.5
                        avg_win = metrics.get('avg_win_pct', 0)
                        avg_loss = abs(metrics.get('avg_loss_pct', 0))
                        sharpe = metrics.get('sharpe_ratio', 0)
                        max_dd = abs(metrics.get('max_dd_pct', 0)) / 100 if metrics.get('max_dd_pct', 0) < 0 else 0.325
                        
                        adv_metrics = statistical_engine.calculate_adjusted_metrics(
                            trades=[{'profit_loss': pnl} for pnl in trades] if trades else [],
                            win_rate=win_rate,
                            avg_win=avg_win,
                            avg_loss=avg_loss,
                            sharpe_ratio=sharpe,
                            max_drawdown=max_dd
                        )
                        
                        # Merge advanced metrics with base metrics
                        metrics['kelly_fraction'] = round(adv_metrics.kelly_fraction, 4)
                        metrics['kelly_position_size'] = round(adv_metrics.kelly_position_size, 2)
                        metrics['bayesian_probability'] = round(adv_metrics.bayesian_probability, 4)
                        metrics['lln_confidence'] = round(adv_metrics.lln_confidence, 4)
                        metrics['clt_normality_pvalue'] = round(adv_metrics.clt_normality_pvalue, 4)
                        metrics['adjusted_sharpe_ratio'] = round(adv_metrics.adjusted_sharpe_ratio, 2)
                        metrics['risk_adjusted_dd'] = round(adv_metrics.risk_adjusted_dd * 100, 2)  # Convert to percentage
                    except Exception as stats_err:
                        logger.warning(f"Statistical analysis failed: {str(stats_err)}")
                        metrics['statistical_error'] = str(stats_err)
                    
                    results[symbol][tf] = metrics
                    summary["successful"] += 1
                    summary["total_tests"] += 1
                    
                    # Track top performers
                    pf = metrics.get("profit_factor", 0)
                    if pf > 1.0:
                        summary["best_performers"].append({
                            "symbol": symbol,
                            "timeframe": tf,
                            "profit_factor": round(pf, 2),
                            "total_return_pct": metrics.get("total_return_pct", 0),
                            "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                            "max_dd_pct": metrics.get("max_dd_pct", 0),
                        })
                
                except Exception as e:
                    results[symbol][tf] = {"error": str(e)}
                    summary["failed"] += 1
                    summary["total_tests"] += 1
        
        # Sort best performers by profit factor
        summary["best_performers"] = sorted(
            summary["best_performers"],
            key=lambda x: x["profit_factor"],
            reverse=True
        )[:5]  # Top 5
        
        # Calculate aggregate statistics
        all_profit_factors = []
        all_returns = []
        all_sharpe = []
        all_max_dd = []
        
        for symbol_data in results.values():
            for tf_data in symbol_data.values():
                if "error" not in tf_data:
                    all_profit_factors.append(tf_data.get("profit_factor", 0))
                    all_returns.append(tf_data.get("total_return_pct", 0))
                    all_sharpe.append(tf_data.get("sharpe_ratio", 0))
                    all_max_dd.append(tf_data.get("max_dd_pct", 0))
        
        aggregate_stats = {
            "avg_profit_factor": round(np.mean(all_profit_factors), 2) if all_profit_factors else 0,
            "median_profit_factor": round(np.median(all_profit_factors), 2) if all_profit_factors else 0,
            "avg_return_pct": round(np.mean(all_returns), 2) if all_returns else 0,
            "avg_sharpe_ratio": round(np.mean(all_sharpe), 2) if all_sharpe else 0,
            "avg_max_dd_pct": round(np.mean(all_max_dd), 2) if all_max_dd else 0,
        }
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "config": {
                "symbols": symbols_list,
                "timeframes": timeframes_list,
                "limit": limit,
                "rsi_buy": rsi_buy,
                "rsi_sell": rsi_sell,
            },
            "summary": summary,
            "aggregate_stats": aggregate_stats,
            "results": results,
            "execution_time_seconds": round(execution_time, 2),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest error: {str(e)}")

# Keep existing endpoints
@router.get("/single-tf")
async def backtest_single_tf(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(1000, ge=100, le=5000),
    rsi_buy: float = Query(60.0, ge=0, le=100),
    rsi_sell: float = Query(70.0, ge=0, le=100),
):
    """Backtest pe un timeframe cu parametri customizabili"""
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

@router.get("/optimize")
async def backtest_optimize(
    symbol: str = Query("BTCUSDT"),
    interval: str = Query("4h"),
    limit: int = Query(1000, ge=100, le=5000),
):
    """Testează multiple RSI parameters și returnează best combination"""
    results = {}
    
    try:
        candles = binance_service.get_candles(symbol, interval, limit)
        if len(candles) < 50:
            raise HTTPException(status_code=400, detail="Insufficient candles")
        
        for rsi_buy in range(30, 70, 5):
            for rsi_sell in range(65, 85, 5):
                if rsi_sell <= rsi_buy:
                    continue
                
                trades, equity_curve = run_backtest(candles, rsi_buy, rsi_sell)
                metrics = calculate_metrics(trades, equity_curve)
                
                key = f"buy_{rsi_buy}_sell_{rsi_sell}"
                results[key] = metrics
        
        best = max(results.items(), key=lambda x: x[1].get("profit_factor", 0))
        best_key = best[0]
        best_metrics = best[1]
        
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
