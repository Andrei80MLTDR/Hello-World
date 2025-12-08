from typing import Dict, List
from app.models.dto import Candle


def calculate_signal(ta_data: Dict, candles: List = None) -> Dict:
    """
    Converteste TA indicators -> probability de miscare UP/DOWN
    
    Input: ta_data = {"trend": "bullish", "ema_fast": X, "ema_slow": Y, "rsi": Z}
    Output: signal cu probability si reasoning
    """
    
    trend = ta_data.get("trend", "neutral")
    trend_score = ta_data.get("trend_score", 0)
    ema_fast = ta_data.get("ema_fast", 0)
    ema_slow = ta_data.get("ema_slow", 0)
    rsi = ta_data.get("rsi", 50)
    
    # Incepe cu base probability
    probability = 0.5  # Neutral
    confidence = 0.5
    reasons = []
    
    # === TREND ANALYSIS ===
    if trend == "bullish":
        probability += 0.15
        confidence += 0.1
        reasons.append("EMA20 > EMA50 (uptrend)")
    elif trend == "bearish":
        probability -= 0.15
        confidence += 0.1
        reasons.append("EMA20 < EMA50 (downtrend)")
    
    # === RSI ANALYSIS ===
    if rsi > 70:
        # Overbought - slight reversal risk
        probability -= 0.05
        confidence += 0.05
        reasons.append(f"RSI {rsi:.1f} (overbought, watch for reversal)")
    elif rsi > 60:
        # Strong momentum
        probability += 0.1
        confidence += 0.1
        reasons.append(f"RSI {rsi:.1f} (strong momentum, bullish bias)")
    elif rsi < 30:
        # Oversold - potential bounce
        probability += 0.05
        confidence += 0.05
        reasons.append(f"RSI {rsi:.1f} (oversold, watch for bounce)")
    elif rsi < 40:
        # Weak momentum
        probability -= 0.1
        confidence += 0.1
        reasons.append(f"RSI {rsi:.1f} (weak momentum, bearish bias)")
    else:
        # Neutral zone
        reasons.append(f"RSI {rsi:.1f} (neutral zone)")
    
    # === VOLUME CHECK (optional, daca avem data) ===
    if candles and len(candles) >= 2:
        recent_volume = float(candles[-1].get("volume", 0) if isinstance(candles[-1], dict) else candles[-1].volume)
        prev_volume = float(candles[-2].get("volume", 0) if isinstance(candles[-2], dict) else candles[-2].volume)
        
        if recent_volume > prev_volume * 1.2:
            probability += 0.05
            confidence += 0.05
            reasons.append("Volume increasing (conviction)")
    
    # === ALIGNMENT STRENGTH ===
    if trend in ["bullish", "bearish"] and rsi not in range(40, 60):
        confidence += 0.1
        reasons.append("Trend and momentum aligned")
    
    # === Clamp values to 0-1 ===
    probability = max(0.0, min(1.0, probability))
    confidence = max(0.0, min(1.0, confidence))
    
    # === Risk/Reward Estimation ===
    # Simplified: bullish trend with good momentum = better R:R
    if probability > 0.65:
        risk_reward = 1.8
    elif probability > 0.6:
        risk_reward = 1.5
    elif probability < 0.35:
        risk_reward = 2.0
    elif probability < 0.4:
        risk_reward = 1.6
    else:
        risk_reward = 1.2
    
    return {
        "probability": round(probability, 3),
        "confidence": round(confidence, 3),
        "trend": trend,
        "reasons": reasons,
        "risk_reward": round(risk_reward, 2),
    }
