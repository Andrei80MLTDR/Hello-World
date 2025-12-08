from typing import List, Dict, Union
from app.models.dto import Candle


def ta_summary(candles: List[Union[Candle, Dict]]) -> Dict:
    """
    Calculeaza indicatori tehnici: EMA20, EMA50, RSI14, trend
    Input: lista de Candle objects SAU dicts
    Output: dict cu indicatori
    """
    
    if not candles or len(candles) < 50:
        return {
            "trend": "insufficient_data",
            "trend_score": 0,
            "ema_fast": 0,
            "ema_slow": 0,
            "rsi": 0,
        }
    
    # Extrage closes (funcționează cu Candle objects și dicts)
    closes = []
    for c in candles:
        if isinstance(c, dict):
            closes.append(float(c.get("close", 0)))
        else:
            closes.append(float(c.close))
    
    if not closes or len(closes) < 50:
        return {
            "trend": "insufficient_data",
            "trend_score": 0,
            "ema_fast": 0,
            "ema_slow": 0,
            "rsi": 0,
        }
    
    # Calculeaza EMA20
    ema_20 = _calculate_ema(closes, 20)
    
    # Calculeaza EMA50
    ema_50 = _calculate_ema(closes, 50)
    
    # Calculeaza RSI14
    rsi_14 = _calculate_rsi(closes, 14)
    
    # Determina trend
    if ema_20 > ema_50 and rsi_14 > 50:
        trend = "bullish"
        trend_score = 0.7
    elif ema_20 < ema_50 and rsi_14 < 50:
        trend = "bearish"
        trend_score = -0.7
    else:
        trend = "neutral"
        trend_score = 0
    
    return {
        "trend": trend,
        "trend_score": trend_score,
        "ema_fast": round(ema_20, 2),
        "ema_slow": round(ema_50, 2),
        "rsi": round(rsi_14, 2),
    }


def _calculate_ema(prices: List[float], period: int) -> float:
    """Calculeaza Exponential Moving Average"""
    if len(prices) < period:
        return 0
    
    # Multiplier
    multiplier = 2 / (period + 1)
    
    # SMA initial
    sma = sum(prices[-period:]) / period
    ema = sma
    
    # Aplica EMA pe restul
    for price in prices[-period + 1:]:
        ema = price * multiplier + ema * (1 - multiplier)
    
    return ema


def _calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculeaza Relative Strength Index"""
    if len(prices) < period + 1:
        return 0
    
    # Calculeaza gains si losses
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # Average gain si loss
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
