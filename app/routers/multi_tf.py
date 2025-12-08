from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.models.dto import Candle
from app.services.binance_ohlc import get_klines
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal

router = APIRouter(prefix="/crypto", tags=["crypto"])


@router.get("/multi-tf")
async def get_multi_timeframe(symbol: str = "BTCUSDT") -> Dict:
    """
    Endpoint CORE: Analiza pe 3 timeframe-uri (1h, 4h, 1d)
    Returnează trend și probability pe fiecare
    """
    try:
        results = {}
        
        # Analizeaza pe fiecare timeframe
        for interval in ["1h", "4h", "1d"]:
            try:
                # Ia candles
                candles = await get_klines(symbol=symbol, interval=interval, limit=150)
                
                # Calculeaza TA
                ta_data = ta_summary(candles)
                
                # Converteste la signal
                signal = calculate_signal(ta_data, candles)
                
                results[interval] = {
                    "trend": signal["trend"],
                    "probability": signal["probability"],
                    "confidence": signal["confidence"],
                    "rsi": ta_data.get("rsi", 0),
                    "ema_fast": ta_data.get("ema_fast", 0),
                    "ema_slow": ta_data.get("ema_slow", 0),
                    "reasons": signal["reasons"][:2],  # Top 2 reasons only
                    "risk_reward": signal["risk_reward"],
                }
            except Exception as e:
                results[interval] = {
                    "error": str(e),
                    "trend": "error",
                    "probability": 0.5,
                }
        
        # === DETERMINE OVERALL BIAS ===
        probabilities = [results[tf]["probability"] for tf in ["1h", "4h", "1d"] if "error" not in results[tf]]
        
        if probabilities:
            avg_probability = sum(probabilities) / len(probabilities)
            if avg_probability > 0.65:
                overall_bias = "STRONG BULLISH"
            elif avg_probability > 0.55:
                overall_bias = "BULLISH"
            elif avg_probability < 0.35:
                overall_bias = "STRONG BEARISH"
            elif avg_probability < 0.45:
                overall_bias = "BEARISH"
            else:
                overall_bias = "NEUTRAL"
        else:
            overall_bias = "UNKNOWN"
        
        # === CHECK ALIGNMENT ===
        trends = [results[tf]["trend"] for tf in ["1h", "4h", "1d"] if "error" not in results[tf]]
        unique_trends = set(trends)
        
        if len(unique_trends) == 1:
            alignment = "PERFECT (all aligned)"
            alignment_strength = 1.0
        elif len(unique_trends) == 2:
            alignment = "GOOD (2 out of 3 aligned)"
            alignment_strength = 0.7
        else:
            alignment = "WEAK (conflicting signals)"
            alignment_strength = 0.3
        
        return {
            "symbol": symbol,
            "timeframes": results,
            "overall_bias": overall_bias,
            "average_probability": round(sum(probabilities) / len(probabilities), 3) if probabilities else 0.5,
            "alignment": alignment,
            "alignment_strength": alignment_strength,
            "timestamp": "current"
        }
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Multi-TF error: {e}")
