import numpy as np
from typing import List, Dict, Optional

def calculate_metrics(trades: List[float], equity_curve: List[float]) -> Dict:
    """
    Calculează metrici avansate de backtest.
    
    Args:
        trades: Lista de PnL pe tranzacție (0.05 = +5%, -0.02 = -2%)
        equity_curve: Lista de equity normalized (1.0, 1.005, 0.99, ...)
    
    Returns:
        Dict cu metricile calculate
    """
    if len(trades) == 0:
        return {
            "error": "No trades executed",
            "total_trades": 0,
            "total_return_pct": 0.0,
        }
    
    trades_arr = np.array(trades)
    equity_arr = np.array(equity_curve)
    
    # === BASIC STATS ===
    total_trades = len(trades_arr)
    wins = int(len(trades_arr[trades_arr > 0]))
    losses = int(len(trades_arr[trades_arr < 0]))
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    
    # === PROFIT METRICS ===
    gross_profit = float(trades_arr[trades_arr > 0].sum()) if len(trades_arr[trades_arr > 0]) > 0 else 0.0
    gross_loss = float(abs(trades_arr[trades_arr < 0].sum())) if len(trades_arr[trades_arr < 0]) > 0 else 0.01
    profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else 0.0
    
    avg_win = float(trades_arr[trades_arr > 0].mean() * 100) if len(trades_arr[trades_arr > 0]) > 0 else 0.0
    avg_loss = float(trades_arr[trades_arr < 0].mean() * 100) if len(trades_arr[trades_arr < 0]) > 0 else 0.0
    
    # === RISK METRICS ===
    # Returns pe perioadă (daily/4h/etc)
    returns = np.diff(equity_arr) / equity_arr[:-1]
    
    # Sharpe Ratio (252 = trading days per year)
    sharpe = 0.0
    if returns.std() > 0:
        sharpe = float((returns.mean() / returns.std()) * np.sqrt(252))
    
    # Sortino Ratio (only downside volatility)
    sortino = sharpe
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 0 and downside_returns.std() > 0:
        sortino = float((returns.mean() / downside_returns.std()) * np.sqrt(252))
    
    # Max Drawdown
    running_max = np.maximum.accumulate(equity_arr)
    drawdowns = (equity_arr - running_max) / running_max
    max_dd = float(np.min(drawdowns) * 100)
    
    # Recovery Factor (return / |max_dd|)
    total_return_pct = float((equity_arr[-1] - 1) * 100)
    recovery_factor = 0.0
    if max_dd != 0:
        recovery_factor = float(total_return_pct / abs(max_dd))
    
    # === CALMAR RATIO ===
    calmar_ratio = 0.0
    if max_dd != 0:
        calmar_ratio = float(total_return_pct / abs(max_dd))
    
    # === CONSECUTIVE WINS/LOSSES ===
    consecutive_wins = 0
    max_consecutive_wins = 0
    consecutive_losses = 0
    max_consecutive_losses = 0
    
    for trade in trades_arr:
        if trade > 0:
            consecutive_wins += 1
            consecutive_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
        else:
            consecutive_losses += 1
            consecutive_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
    
    return {
        "total_trades": int(total_trades),
        "wins": int(wins),
        "losses": int(losses),
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "max_consecutive_wins": int(max_consecutive_wins),
        "max_consecutive_losses": int(max_consecutive_losses),
        "gross_profit_pct": round(gross_profit * 100, 2),
        "gross_loss_pct": round(gross_loss * 100, 2),
        "max_dd_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "calmar_ratio": round(calmar_ratio, 2),
        "recovery_factor": round(recovery_factor, 2),
        "total_return_pct": round(total_return_pct, 2),
    }


def compare_timeframes(results: Dict[str, Dict]) -> Dict:
    """Compară rezultate între timeframe-uri și returnează best performer"""
    if not results:
        return {"error": "No results to compare"}
    
    best_tf = max(results.items(), key=lambda x: x[1].get("profit_factor", 0))
    best_sharpe_tf = max(results.items(), key=lambda x: x[1].get("sharpe_ratio", -999))
    
    return {
        "best_by_profit_factor": {
            "timeframe": best_tf[0],
            "profit_factor": best_tf[1].get("profit_factor", 0),
        },
        "best_by_sharpe": {
            "timeframe": best_sharpe_tf[0],
            "sharpe_ratio": best_sharpe_tf[1].get("sharpe_ratio", 0),
        },
        "all_timeframes": list(results.keys()),
    }
