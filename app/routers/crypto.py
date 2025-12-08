from app.models.dto import PriceResponse, Candle, TASummary
from app.services.binance_client import get_binance_price
from app.services.binance_ohlc import get_klines
from app.services.ta_engine import ta_summary

import os

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")

ECON_API_KEY = os.getenv("ECON_API_KEY", "")
