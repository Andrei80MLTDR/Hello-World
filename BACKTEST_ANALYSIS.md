# Backtesting System - Large-Scale Analysis

## Overview
FastAPI-based backtesting system for cryptocurrency trading strategies with support for multiple symbols, timeframes, and comprehensive performance metrics.

## New Feature: Large-Scale Backtesting Endpoint

### Endpoint: `/backtest/large-scale`

**Method**: GET

**Description**: Execute backtesting across multiple symbols and timeframes simultaneously to stress-test the system and identify top-performing strategy combinations.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `symbols` | str | BTCUSDT,ETHUSDT,XRPUSDT | CSV list | Trading pairs (BTCUSDT,ETHUSDT,ADAUSDT,DOGEUSDT) |
| `timeframes` | str | 4h,1d | CSV list | Timeframes to test (1h,4h,1d,1w) |
| `limit` | int | 2000 | 500-5000 | Candles per symbol/timeframe |
| `rsi_buy` | float | 45.0 | 20-80 | Entry signal threshold (lower = more aggressive) |
| `rsi_sell` | float | 65.0 | 20-80 | Exit signal threshold (higher = more aggressive) |

### Example Usage

```bash
# Test 3 symbols across 2 timeframes
GET /backtest/large-scale?symbols=BTCUSDT,ETHUSDT,XRPUSDT&timeframes=4h,1d&limit=1000&rsi_buy=50&rsi_sell=70

# Aggressive strategy on major pairs
GET /backtest/large-scale?symbols=BTCUSDT,ETHUSDT&timeframes=4h,1d,1w&limit=2000&rsi_buy=35&rsi_sell=75
```

### Response Structure

```json
{
  "status": "completed",
  "config": {
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "timeframes": ["4h", "1d"],
    "limit": 1000,
    "rsi_buy": 50,
    "rsi_sell": 70
  },
  "summary": {
    "total_tests": 4,
    "successful": 4,
    "failed": 0,
    "best_performers": [
      {
        "symbol": "BTCUSDT",
        "timeframe": "4h",
        "profit_factor": 1.85,
        "total_return_pct": 24.5,
        "sharpe_ratio": 1.42,
        "max_dd_pct": -12.3
      }
    ]
  },
  "aggregate_stats": {
    "avg_profit_factor": 1.62,
    "median_profit_factor": 1.70,
    "avg_return_pct": 18.3,
    "avg_sharpe_ratio": 1.25,
    "avg_max_dd_pct": -14.5
  },
  "results": {...},
  "execution_time_seconds": 12.4
}
```

## Performance Metrics Included

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| **Profit Factor** | Gross profit / Gross loss | >1.5 = Good, >2.0 = Excellent |
| **Win Rate %** | Percentage of winning trades | >50% = Positive edge |
| **Sharpe Ratio** | Return / volatility * sqrt(252) | >1.0 = Good, >2.0 = Excellent |
| **Sortino Ratio** | Return / downside volatility | Focuses on negative volatility |
| **Max Drawdown %** | Peak-to-trough decline | Measures risk exposure |
| **Calmar Ratio** | Annual return / max drawdown | Higher is better |
| **Recovery Factor** | Total return / max drawdown | Ability to recover from losses |
| **Total Return %** | Overall strategy gain/loss | Self-explanatory |

## System Limits & Constraints

### API Limits
- **Max candles per request**: 5,000 (Binance API limit)
- **Max symbols per batch**: Unlimited (tested with 3-10)
- **Max timeframes per symbol**: 4 recommended (1h, 4h, 1d, 1w)
- **Timeout**: 60 seconds per request (Render free tier)

### Performance Characteristics

**2 symbols × 2 timeframes × 1000 candles**: ~2-3 seconds
**5 symbols × 2 timeframes × 2000 candles**: ~8-12 seconds
**10 symbols × 3 timeframes × 2000 candles**: ~25-35 seconds

### Memory Usage
- Each 1000-candle backtest: ~2-3 MB
- Aggregate calculations: Minimal overhead
- Expected: <100 MB for large-scale test

### Strategy Constraints
- **Min candles**: 50 (for TA indicators)
- **Window calculation**: All TA indicators use rolling window
- **Entry logic**: RSI < rsi_buy + Bullish signal
- **Exit logic**: RSI > rsi_sell OR Bearish signal
- **Position**: Single entry/exit per cycle

## Best Practices

### For Swing Trading (4h - 1d)
1. Start with moderate RSI parameters (45-50 buy, 65-75 sell)
2. Test on 500-1000 historical candles
3. Focus on profit_factor > 1.5
4. Accept max_dd < -20%

### For Aggressive Strategies (1h)
1. Use lower timeframe limits (500-1000)
2. Accept higher drawdowns (-25% to -40%)
3. Focus on consistent win rate (>55%)

### Parameter Optimization Tips
1. Start conservative, gradually reduce rsi_buy (more entries)
2. Use large-scale endpoint to scan parameters
3. Sort by sharpe_ratio for risk-adjusted returns
4. Verify results across multiple timeframes

## Real-World Expectations

✅ **What works**:
- Profit factors 1.2 - 2.5 are realistic
- Win rates 45-60% are typical
- Max drawdowns 10-25% are common

⚠️ **Backtesting pitfalls**:
- Past performance ≠ future results
- No slippage/commission modeled
- No real liquidity/spread simulation
- Perfect execution assumed

## Deployment Status

**API URL**: https://personal-hedge-fund-api.onrender.com
**Status**: ✅ Live on Render free tier
**Endpoints Available**:
- `/health` - Service health check
- `/backtest/large-scale` - NEW: Multi-symbol batch testing
- `/backtest/single-tf` - Single symbol/timeframe
- `/backtest/optimize` - Parameter optimization
- `/backtest/multi-tf` - Compare timeframes
- `/backtest/batch` - Custom batches
- `/backtest/stats` - Quick statistics

## Development Notes

**Last Updated**: Dec 9, 2025
**Author**: Andrei80MLTDR
**Framework**: FastAPI
**Data Source**: Binance REST API
**Strategy**: RSI + Direction signal (TA engine)
**Metrics**: Advanced (Sharpe, Sortino, Calmar, Recovery Factor)
