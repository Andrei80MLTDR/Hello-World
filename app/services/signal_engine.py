from typing import Dict
import numpy as np


def calculate_signal(ta_data: Dict, current_price: float) -> Dict:
    """Calculate trading signal from technical analysis indicators"""
    try:
        if not ta_data:
            return _neutral_signal()
        
        rsi = ta_data.get("rsi", 50)
        macd = ta_data.get("macd", {})
        stoch = ta_data.get("stochastic", {})
        cci = ta_data.get("cci", 0)
        ema_fast = ta_data.get("ema_fast", 0)
        ema_slow = ta_data.get("ema_slow", 0)
        
        bullish_score = 0
        bearish_score = 0
        signal_strength = 0
        
        if rsi < 30:
            bullish_score += 2
            signal_strength += 1
        elif rsi < 40:
            bullish_score += 1
        elif rsi > 70:
            bearish_score += 2
            signal_strength += 1
        elif rsi > 60:
            bearish_score += 1
        
        macd_hist = macd.get("histogram", 0)
        if macd_hist > 0:
            bullish_score += 1.5
            if macd_hist > 0.001:
                bullish_score += 0.5
        else:
            bearish_score += 1.5
            if macd_hist < -0.001:
                bearish_score += 0.5
        signal_strength += 0.5
        
        stoch_k = stoch.get("k", 50)
        stoch_signal = stoch.get("signal", "neutral")
        
        if stoch_signal == "oversold":
            bullish_score += 1.5
            signal_strength += 0.5
        elif stoch_signal == "overbought":
            bearish_score += 1.5
            signal_strength += 0.5
        
        if abs(cci) > 100:
            signal_strength += 1
            if cci > 100:
                bullish_score += 1
            else:
                bearish_score += 1
        
        if ema_fast > 0 and ema_slow > 0:
            if ema_fast > ema_slow:
                bullish_score += 2
                signal_strength += 1
            else:
                bearish_score += 2
                signal_strength += 1
        
        total_score = bullish_score + bearish_score
        if total_score == 0:
            return _neutral_signal()
        
        bullish_prob = (bullish_score / total_score) * 100
        
        if bullish_prob > 65:
            trend = "BULLISH"
            probability = min(bullish_prob, 95)
        elif bullish_prob < 35:
            trend = "BEARISH"
            probability = min((100 - bullish_prob), 95)
        else:
            trend = "NEUTRAL"
            probability = 50
        
        confidence = min(signal_strength * 10, 100)
        
        if trend == "BULLISH":
            risk_reward = 1.5 + (confidence / 100)
        elif trend == "BEARISH":
            risk_reward = 1.5 + (confidence / 100)
        else:
            risk_reward = 1.0
        
        return {
            "trend": trend,
            "probability": round(probability, 1),
            "confidence": round(confidence, 1),
            "signal_strength": round(signal_strength, 2),
            "risk_reward": round(risk_reward, 2),
            "rsi": round(rsi, 1),
            "macd_direction": macd.get("direction", "neutral"),
            "stochastic_signal": stoch_signal,
            "timestamp": str(np.datetime64('now'))
        }
    except Exception as e:
        print(f"Error calculating signal: {e}")
        return _neutral_signal()


def _neutral_signal() -> Dict:
    return {
        "trend": "NEUTRAL",
        "probability": 50.0,
        "confidence": 0.0,
        "signal_strength": 0.0,
        "risk_reward": 1.0,
        "rsi": 50.0,
        "macd_direction": "neutral",
        "stochastic_signal": "neutral",
        "timestamp": str(np.datetime64('now'))
    }
