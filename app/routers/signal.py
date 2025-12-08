from fastapi import APIRouter, HTTPException
from app.models.dto import SignalResponse, Candle
from app.services.binance_ohlc import get_klines
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal

router = APIRouter(prefix="/crypto", tags=["crypto"])


@router.get("/signal", response_model=SignalResponse)
async def get_signal(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 150,
):
    """
    Endpoint care returnează SIGNAL cu probabilitate de miscare UP/DOWN
    """
    try:
        # Ia candles din Binance
        candles = await get_klines(symbol=symbol, interval=interval, limit=limit)
        
        # Calculeaza TA
        ta_data = ta_summary(candles)
        
        # Converteste TA -> Signal cu probability
        signal = calculate_signal(ta_data, candles)
        
        # Combine in response
        return SignalResponse(
            symbol=symbol,
            interval=interval,
            probability=signal["probability"],
            confidence=signal["confidence"],
            trend=signal["trend"],
            reasons=signal["reasons"],
            risk_reward=signal["risk_reward"],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Signal calculation error: {e}")
