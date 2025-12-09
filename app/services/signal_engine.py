from typing import List, Dict, Union
from app.models.dto import Candle


def calculate_signal(candles: List[Candle], ta: Dict) -> Dict:
    """
    Calculates trading signal based on candles and technical analysis indicators.
    
    Args:
        candles: List of Candle objects
        ta: Dictionary with TA indicators (from ta_summary)
    
    Returns:
        Dictionary with signal info
    """
    
    # Extract indicators safely from ta dict
    rsi = float(ta.get("rsi", 50))
    ema_fast = float(ta.get("ema_fast", 0))
    ema_slow = float(ta.get("ema_slow", 0))
    macd = float(ta.get("macd", 0))
    macd_signal = float(ta.get("macd_signal", 0))
    bb_upper = float(ta.get("bb_upper", 0))
    bb_lower = float(ta.get("bb_lower", 0))
    
    # Initialize signal
    direction = "neutral"
    score = 0.0
    
    # EMA-based logic
    if ema_fast > ema_slow:
        score += 0.5
        direction = "bullish"
    elif ema_fast < ema_slow:
        score -= 0.5
        direction = "bearish"
    
    # RSI-based logic
    if rsi > 70:
        score -= 0.5
    elif rsi < 30:
        score += 0.5
    
    # MACD-based logic (optional)
    if macd > macd_signal:
        score += 0.3
    elif macd < macd_signal:
        score -= 0.3
    
    # Bollinger Bands logic (optional)
    if candles:
        current_close = float(candles[-1].close)
        if current_close > bb_upper:
            score -= 0.2
        elif current_close < bb_lower:
            score += 0.2
    
    # Clamp score to [-1, 1]
    score = max(-1.0, min(1.0, score))
    
    return {
        "direction": direction,
        "score": round(score, 2),
        "rsi": round(rsi, 2),
        "ema_fast": round(ema_fast, 2),
        "ema_slow": round(ema_slow, 2),
        "macd": round(macd, 2),
        "macd_signal": round(macd_signal, 2),
        "bb_upper": round(bb_upper, 2),
        "bb_lower": round(bb_lower, 2),
    }
