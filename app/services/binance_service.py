import requests
from typing import List
from app.models.dto import Candle


class BinanceService:
    """Binance API client for fetching OHLCV data"""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        if testnet:
            self.BASE_URL = "https://testnet.binance.vision/api/v3"

    def get_raw_klines(self, symbol: str, interval: str, limit: int = 500) -> list:
        """
        Fetch raw klines array from Binance (as returned by API).
        """
        url = f"{self.BASE_URL}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_candles(self, symbol: str, interval: str, limit: int = 500) -> List[Candle]:
        """
        Fetch klines from Binance and map them into a list of Candle models.
        """
        raw_klines = self.get_raw_klines(symbol, interval, limit)
        candles: List[Candle] = []

        for k in raw_klines:
            # Binance kline format:
            # [0] open time (ms), [1] open, [2] high, [3] low, [4] close, [5] volume, ...
            try:
                candle = Candle(
                    open_time=int(k[0]),
                    open=float(k[1]),
                    high=float(k[2]),
                    low=float(k[3]),
                    close=float(k[4]),
                    volume=float(k[5]),
                )
                candles.append(candle)
            except (ValueError, IndexError):
                # Skip any malformed kline
                continue

        return candles
