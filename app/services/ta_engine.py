from typing import List, Dict
import math

def compute_ema(values: List[float], period: int) -> List[float]:
    if not values or period <= 0:
        return []
    k = 2 / (period + 1)
    emas: List[float] = []
    ema_prev = sum(values[:period]) / period
    emas.extend([math.nan] * (period - 1))
    emas.append(ema_prev)
    for price in values[period:]:
        ema_prev = price * k + ema_prev * (1 - k)
        emas.append(ema_prev)
    return emas

def compute_rsi(values: List[float], period: int = 14) -> List[float]:
    if len(values) < period + 1:
        return [math.nan] * len(values)
    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, period + 1):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rsis: List[float] = [math.nan] * period
    for i in range(period + 1, len(values)):
        diff = values[i] - values[i - 1]
        gain = max(diff, 0)
        loss = max(-diff, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            rs = math.inf
        else:
            rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsis.append(rsi)
    while len(rsis) < len(values):
        rsis.append(math.nan)
    return rsis

def ta_summary(candles: List[Dict]) -> Dict:
    if not candles:
        return {
            "trend": "neutral",
            "trend_score": 0.5,
            "ema_fast": None,
            "ema_slow": None,
            "rsi": None,
        }

    closes = [c["close"] for c in candles]
    ema_fast_list = compute_ema(closes, period=20)
    ema_slow_list = compute_ema(closes, period=50)
    rsi_list = compute_rsi(closes, period=14)

    ema_fast = ema_fast_list[-1]
    ema_slow = ema_slow_list[-1]
    rsi = rsi_list[-1]

    trend_score = 0.5
    if not math.isnan(ema_fast) and not math.isnan(ema_slow):
        if ema_fast > ema_slow:
            trend_score += 0.2
        elif ema_fast < ema_slow:
            trend_score -= 0.2

    if not math.isnan(rsi):
        if rsi > 60:
            trend_score += 0.2
        elif rsi < 40:
            trend_score -= 0.2

    trend_score = max(0.0, min(1.0, trend_score))

    if trend_score > 0.6:
        trend = "bullish"
    elif trend_score < 0.4:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "trend": trend,
        "trend_score": trend_score,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "rsi": rsi,
    }
