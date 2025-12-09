from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List
from app.models.dto import Candle
from app.services.binance_ohlc import get_klines
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal
from fastapi import FastAPI
from app.routers import crypto, news, signal, multi_tf, backtest

app = FastAPI()
app.include_router(crypto.router)
app.include_router(news.router)
app.include_router(signal.router)
app.include_router(multi_tf.router)
app.include_router(backtest.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
