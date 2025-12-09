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
    
    # Extract MACD values from nested dict
    macd_dict = ta.get("macd", {})
    macd = float(macd_dict.get("macd", 0)) if isinstance(macd_dict, dict) else 0.0
    macd_signal = float(macd_dict.get("signal", 0)) if isinstance(macd_dict, dict) else 0.0
    
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
    
    # MACD-based logic
    if macd > macd_signal:
        score += 0.3
    elif macd < macd_signal:
        score -= 0.3
    
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
    }
