from typing import List, Dict, Union
from app.models.dto import Candle


def calculate_signal(candles: List[Candle], ta: Union[Dict, None] = None) -> Dict:
    """
    Calculates trading signal based on candles and technical analysis.
    
    Args:
        candles: List of Candle objects
        ta: Dictionary with TA indicators (from ta_summary)
    
    Returns:
        Dictionary with signal info
    """
    # Defensive: ensure ta is a dict, not list or None
    if ta is None or not isinstance(ta, dict):
        ta = {}
    
    # Extract indicators safely with defaults
    rsi = float(ta.get("rsi", 50.0))
    ema_fast = float(ta.get("ema_fast", 0.0))
    ema_slow = float(ta.get("ema_slow", 0.0))
    macd = ta.get("macd", 0.0)
    signal_line = ta.get("signal_line", 0.0)
    
    # Initialize signal
    direction = "neutral"
    score = 0.0
    
    # EMA-based logic
    if ema_fast > 0 and ema_slow > 0:
        if ema_fast > ema_slow:
            score += 0.5
            direction = "bullish"
        elif ema_fast < ema_slow:
            score -= 0.5
            direction = "bearish"
    
    # RSI-based logic
    if rsi > 70:
        score -= 0.3
    elif rsi < 30:
        score += 0.3
    
    # MACD-based logic (optional)
    if isinstance(macd, (int, float)) and isinstance(signal_line, (int, float)):
        if macd > signal_line:
            score += 0.2
        elif macd < signal_line:
            score -= 0.2
    
    return {
        "direction": direction,
        "score": round(score, 2),
        "rsi": round(rsi, 2),
        "ema_fast": round(ema_fast, 2),
        "ema_slow": round(ema_slow, 2),
    }
