from typing import List, Dict, Union
from app.models.dto import Candle
import yfinance as yf


def safe_float(value) -> float:
    try:
        return float(value)
    except:
        return 0.0


def get_value(item: Union[Candle, Dict], key: str) -> float:
    if isinstance(item, dict):
        return safe_float(item.get(key, 0))
    else:
        return safe_float(getattr(item, key, 0))



def fetch_yahoo_ohlcv(symbol: str, interval: str = "1d", limit: int = 500) -> List[Dict]:
    """
    Fetch OHLCV for stocks via yfinance and return list of dicts
    compatible with Candle / ta_engine.
    """
    tf_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "60m",
        "4h": "240m",
        "1d": "1d",
    }
    yf_interval = tf_map.get(interval, "1d")

    try:
        df = yf.download(
            tickers=symbol,
            period="max",
            interval=yf_interval,
            auto_adjust=False,
            progress=False,
        ).tail(limit)

        candles: List[Dict] = []
        for ts, row in df.iterrows():
            candles.append(
                {
                    "open_time": int(ts.timestamp() * 1000),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                }
            )
        return candles
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


STOCK_SYMBOLS = {"AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA", "NFLX", "AMD", "TSLA"}


def get_ohlcv(symbol: str, interval: str, limit: int) -> List[Dict]:
    """
    Route OHLCV requests to appropriate data source.
    Stocks go to Yahoo, crypto to your existing Binance fetcher.
    """
    if symbol.upper() in STOCK_SYMBOLS:
        return fetch_yahoo_ohlcv(symbol, interval, limit)
    else:
        # For now, we only support stocks via yfinance
        # TODO: Add Binance fetcher here if needed
        return []


def calculate_ema(closes: List[float], period: int) -> float:
    if not closes or len(closes) < period:
        return closes[-1] if closes else 0
    try:
        k = 2 / (period + 1)
        ema = closes[0]
        for price in closes[1:]:
            ema = price * k + ema * (1 - k)
        return ema
    except:
        return closes[-1] if closes else 0


def calculate_rsi_wilders(closes: List[float], period: int = 14) -> float:
    try:
        if not closes or len(closes) < period + 1:
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
    except:
        return 50.0


def calculate_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    try:
        if not closes or len(closes) < slow:
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
        return {"macd": round(macd_line, 6), "signal": round(signal_line, 6), "histogram": round(histogram, 6), "direction": "bullish" if histogram > 0 else "bearish"}
    except:
        return {"macd": 0, "signal": 0, "histogram": 0, "direction": "neutral"}


def calculate_stochastic(closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> Dict:
    try:
        if not closes or len(closes) < period:
            return {"k": 50, "d": 50, "signal": "neutral"}
        highest_high = max(highs[-period:]) if highs[-period:] else closes[-1]
        lowest_low = min(lows[-period:]) if lows[-period:] else closes[-1]
        k = 100 * (closes[-1] - lowest_low) / (highest_high - lowest_low) if highest_high != lowest_low else 50
        k_values = []
        for i in range(len(closes) - period + 1, len(closes) + 1):
            try:
                high = max(highs[i-period:i])
                low = min(lows[i-period:i])
                k_val = 100 * (closes[i-1] - low) / (high - low) if high != low else 50
                k_values.append(k_val)
            except:
                pass
        d = sum(k_values[-3:]) / 3 if len(k_values) >= 3 else k
        signal = "overbought" if k > 80 else "oversold" if k < 20 else "neutral"
        return {"k": round(k, 2), "d": round(d, 2), "signal": signal}
    except:
        return {"k": 50, "d": 50, "signal": "neutral"}


def calculate_cci(closes: List[float], period: int = 20) -> float:
    try:
        if not closes or len(closes) < period:
            return 0
        recent = closes[-period:]
        tp = sum(recent) / len(recent)
        mean_dev = sum(abs(price - tp) for price in recent) / len(recent)
        if mean_dev == 0:
            return 0
        cci = (closes[-1] - tp) / (0.015 * mean_dev)
        return round(cci, 2)
    except:
        return 0


def calculate_vwap_session(candles: Union[List[Candle], List[Dict]]) -> float:
    try:
        if not candles:
            return 0
        cumulative_tp_vol = 0
        cumulative_vol = 0
        for candle in candles:
            try:
                high = get_value(candle, "high")
                low = get_value(candle, "low")
                close = get_value(candle, "close")
                volume = get_value(candle, "volume")
                typical_price = (high + low + close) / 3
                cumulative_tp_vol += typical_price * volume
                cumulative_vol += volume
            except:
                continue
        if cumulative_vol == 0:
            return safe_float(get_value(candles[-1], "close")) if candles else 0
        return round(cumulative_tp_vol / cumulative_vol, 2)
    except:
        return 0


def get_vwap_levels(candles: Union[List[Candle], List[Dict]]) -> Dict:
    try:
        if not candles:
            return {"daily": 0, "weekly": 0, "monthly": 0, "quarterly": 0, "yearly": 0}
        return {
            "daily": calculate_vwap_session(candles[-24:] if len(candles) >= 24 else candles),
            "weekly": calculate_vwap_session(candles[-168:] if len(candles) >= 168 else candles),
            "monthly": calculate_vwap_session(candles[-720:] if len(candles) >= 720 else candles),
            "quarterly": calculate_vwap_session(candles[-2160:] if len(candles) >= 2160 else candles),
            "yearly": calculate_vwap_session(candles)
        }
    except:
        return {"daily": 0, "weekly": 0, "monthly": 0, "quarterly": 0, "yearly": 0}



def calculate_atr(candles: Union[List[Candle], List[Dict]], period: int = 14) -> float:
    """Calculate Average True Range (ATR) for volatility-based stop loss"""
    try:
        if not candles or len(candles) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(candles)):
            high = get_value(candles[i], "high")
            low = get_value(candles[i], "low")
            prev_close = get_value(candles[i-1], "close")
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if not true_ranges:
            return 0.0
        
        # Calculate ATR using Wilder's smoothing method
        atr = sum(true_ranges[:period]) / period
        for i in range(period, len(true_ranges)):
            atr = ((atr * (period - 1)) + true_ranges[i]) / period
        
        return round(atr, 2)
    except:
        return 0.0
def ta_summary(candles: Union[List[Candle], List[Dict]]) -> Dict:
    try:
        if not candles or len(candles) < 50:
            return {"ema_fast": 0, "ema_slow": 0, "rsi": 50, "macd": {"macd": 0, "signal": 0, "histogram": 0, "direction": "neutral"}, "stochastic": {"k": 50, "d": 50, "signal": "neutral"}, "cci": 0, "vwap": {"daily": 0, "weekly": 0, "monthly": 0, "quarterly": 0, "yearly": 0}}
        closes = [get_value(c, "close") for c in candles]
        highs = [get_value(c, "high") for c in candles]
        lows = [get_value(c, "low") for c in candles]
        ema_fast = calculate_ema(closes, 20)
        ema_slow = calculate_ema(closes, 50)
        rsi = calculate_rsi_wilders(closes, period=14)
                atr = calculate_atr(candles, period=14)
    return {"ema_fast": round(ema_fast, 2), "ema_slow": round(ema_slow, 2), "rsi": round(rsi, 2), "macd": calculate_macd(closes), "stochastic": calculate_stochastic(closes, highs, lows), "cci": calculate_cci(closes), "vwap": get_vwap_levels(candles)}, "atr": atr
    except Exception as e:
        print(f"Error in ta_summary: {e}")
        return {"ema_fast": 0, "ema_slow": 0, "rsi": 50, "macd": {"macd": 0, "signal": 0, "histogram": 0, "direction": "neutral"}, "stochastic": {"k": 50, "d": 50, "signal": "neutral"}, "cci": 0, "vwap": {"daily": 0, "weekly": 0, "monthly": 0, "quarterly": 0, "yearly":, "atr": 0 0}}
