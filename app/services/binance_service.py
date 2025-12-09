import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time


class BinanceService:
    """Binance API client for fetching OHLCV data"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        if testnet:
            self.BASE_URL = "https://testnet.binance.vision/api/v3"
    
    def get_klines(self, symbol: str, interval: str, limit: int = 200, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[List]:
        try:
            params = {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)}
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
            response = requests.get(f"{self.BASE_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            return response.json() if response.json() else []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return []
    
    def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        try:
            response = requests.get(f"{self.BASE_URL}/ticker/24hr", params={"symbol": symbol}, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            response = requests.get(f"{self.BASE_URL}/ticker/price", params={"symbol": symbol}, timeout=10)
            response.raise_for_status()
            return float(response.json().get("price", 0))
        except:
            return None
    
    def get_exchange_info(self) -> Optional[Dict]:
        try:
            response = requests.get(f"{self.BASE_URL}/exchangeInfo", timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def get_historical_data(self, symbol: str, interval: str, days: int = 30) -> List[List]:
        try:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            all_klines = []
            current_start = start_time
            while current_start < end_time:
                klines = self.get_klines(symbol=symbol, interval=interval, limit=1000, start_time=current_start, end_time=end_time)
                if not klines:
                    break
                all_klines.extend(klines)
                current_start = int(klines[-1][0]) + 1
                time.sleep(0.1)
            return all_klines
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return []
    
    @staticmethod
    def interval_to_minutes(interval: str) -> int:
        intervals = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720, "1d": 1440, "3d": 4320, "1w": 10080, "1M": 43200}
        return intervals.get(interval, 60)
