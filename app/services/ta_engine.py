from typing import List, Dict
from app.models.dto import Candle
import statistics


def calculate_ema(closes: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(closes) < period:
        return closes[-1] if closes else 0
    
    k = 2 / (period + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = price * k + ema * (1 - k)
    return ema


def calculate_rsi_wilders(closes: List[float], period: int = 14) -> float:
    """RSI calculat cu Wilder's smoothing (metoda TradingView)"""
    if len(closes) < period + 1:
        return 50.0
    
    deltas = []
    for i in range(1, len(closes)):
        deltas.append(closes[i] - closes[i-1])
    
    seed = sum(deltas[:period]) / period
    up = seed if seed > 0 else 0
    down = -seed if seed < 0 else 0
    
    rs_list = [0]
    for i in range(period, len(deltas)):
        delta = deltas[i]
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        
        rs = up / down if down != 0 else 0
        rs_list.append(100 - 100 / (1 + rs))
    
    return rs_list[-1] if rs_list else 50.0


def calculate_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """MACD: trend-following momentum indicator"""
    if len(closes) < slow:
        return {"macd": 0, "signal": 0, "histogram": 0, "direction": "neutral"}
    
    ema_fast = [closes[0]]
    ema_slow = [closes[0]]
    k_fast = 2 / (fast + 1)
    k_slow = 2 / (slow + 1)
    
    for price in closes[1:]:
        ema_fast.append(price * k_fast + ema_fast[-1] * (1 - k_fast))
        ema_slow.append(price * k_slow + ema_slow[-1] * (1 - k_slow))
    
    macd_line = ema_fast[-1] - ema_slow[-1]
    
    macd_values = [ema_fast[i] - ema_slow[i] for i in range(len(ema_fast))]
    signal_line = macd_values[-1]
    for i in range(len(macd_values) - signal + 1, len(macd_values)):
        signal_line = macd_values[i] * (2 / (signal + 1)) + signal_line * (1 - 2 / (signal + 1))
    
    histogram = macd_line - signal_line
    
    return {
        "macd": round(macd_line, 6),
        "signal": round(signal_line, 6),
        "histogram": round(histogram, 6),
        "direction": "bullish" if histogram > 0 else "bearish"
    }


def calculate_stochastic(closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> Dict:
    """Stochastic Oscillator: momentum indicator"""
    if len(closes) < period:
        return {"k": 50, "d": 50, "signal": "neutral"}
    
    recent_closes = closes[-period:]
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    
    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    
    k = 100 * (closes[-1] - lowest_low) / (highest_high - lowest_low) if highest_high != lowest_low else 50
    
    k_values = []
    for i in range(len(closes) - period + 1, len(closes) + 1):
        high = max(highs[i-period:i])
        low = min(lows[i-period:i])
        k_val = 100 * (closes[i-1] - low) / (high - low) if high != low else 50
        k_values.append(k_val)
    
    d = sum(k_values[-3:]) / 3 if len(k_values) >= 3 else k
    
    if k > 80:
        signal = "overbought"
    elif k < 20:
        signal = "oversold"
    else:
        signal = "neutral"
    
    return {
        "k": round(k, 2),
        "d": round(d, 2),
        "signal": signal
    }


def calculate_cci(closes: List[float], period: int = 20) -> float:
    """CCI: Commodity Channel Index - momentum indicator"""
    if len(closes) < period:
        return 0
    
    recent = closes[-period:]
    tp = sum(recent) / len(recent)
    
    mean_dev = sum(abs(price - tp) for price in recent) / len(recent)
    
    if mean_dev == 0:
        return 0
    
    cci = (closes[-1] - tp) / (0.015 * mean_dev)
    return round(cci, 2)


def calculate_vwap_session(candles: List[Candle]) -> float:
    """VWAP: Volume Weighted Average Price"""
    if not candles:
        return 0
    
    cumulative_tp_vol = 0
    cumulative_vol = 0
    
    for candle in candles:
        typical_price = (float(candle.high) + float(candle.low) + float(candle.close)) / 3
        volume = float(candle.volume)
        
        cumulative_tp_vol += typical_price * volume
        cumulative_vol += volume
    
    if cumulative_vol == 0:
        return float(candles[-1].close)
    
    vwap = cumulative_tp_vol / cumulative_vol
    return round(vwap, 2)


def get_vwap_levels(candles: List[Candle]) -> Dict:
    """Calculate VWAP for multiple time periods"""
    
    daily_candles = candles[-24:] if len(candles) >= 24 else candles
    weekly_candles = candles[-168:] if len(candles) >= 168 else candles
    monthly_candles = candles[-720:] if len(candles) >= 720 else candles
    quarterly_candles = candles[-2160:] if len(candles) >= 2160 else candles
    yearly_candles = candles
    
    return {
        "daily": calculate_vwap_session(daily_candles),
        "weekly": calculate_vwap_session(weekly_candles),
        "monthly": calculate_vwap_session(monthly_candles),
        "quarterly": calculate_vwap_session(quarterly_candles),
        "yearly": calculate_vwap_session(yearly_candles),
    }


def ta_summary(candles: List[Candle]) -> Dict:
    """Comprehensive technical analysis"""
    if not candles:
        return {}
    
    closes = [float(c.close) for c in candles]
    highs = [float(c.high) for c in candles]
    lows = [float(c.low) for c in candles]
    
    ema_fast = calculate_ema(closes, 20)
    ema_slow = calculate_ema(closes, 50)
    rsi = calculate_rsi_wilders(closes, period=14)
    
    return {
        "ema_fast": round(ema_fast, 2),
        "ema_slow": round(ema_slow, 2),
        "rsi": round(rsi, 2),
        "macd": calculate_macd(closes),
        "stochastic": calculate_stochastic(closes, highs, lows),
        "cci": calculate_cci(closes),
        "vwap": get_vwap_levels(candles),
    }
