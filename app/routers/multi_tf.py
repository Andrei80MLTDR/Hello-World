from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, List
from app.models.dto import Candle
from app.services.binance_ohlc import get_klines
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal

router = APIRouter(prefix="/crypto", tags=["crypto"])


@router.get("/multi-tf")
async def get_multi_timeframe(
    symbol: str = "BTCUSDT",
    format: str = "json"
) -> Dict:
    """
    Endpoint CORE: Analiza pe 3 timeframe-uri (1h, 4h, 1d)
    format=json → JSON frumos
    format=html → Dashboard vizual
    """
    try:
        results = {}
        
        # Analizeaza pe fiecare timeframe
        for interval in ["1h", "4h", "1d"]:
            try:
                candles = await get_klines(symbol=symbol, interval=interval, limit=150)
                ta_data = ta_summary(candles)
                signal = calculate_signal(ta_data, candles)
                
                results[interval] = {
                    "trend": signal["trend"],
                    "probability": signal["probability"],
                    "confidence": signal["confidence"],
                    "rsi": ta_data.get("rsi", 0),
                    "ema_fast": ta_data.get("ema_fast", 0),
                    "ema_slow": ta_data.get("ema_slow", 0),
                    "reasons": signal["reasons"][:2],
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
        
        response_data = {
            "symbol": symbol,
            "timeframes": results,
            "overall_bias": overall_bias,
            "average_probability": round(sum(probabilities) / len(probabilities), 3) if probabilities else 0.5,
            "alignment": alignment,
            "alignment_strength": alignment_strength,
            "timestamp": "current"
        }
        
        # Return HTML dashboard if requested
        if format.lower() == "html":
            return HTMLResponse(content=_generate_html_dashboard(response_data))
        
        # Default: return formatted JSON
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Multi-TF error: {e}")


def _generate_html_dashboard(data: Dict) -> str:
    """Genereaza HTML dashboard frumos pentru multi-TF"""
    
    bias_color = {
        "STRONG BULLISH": "#00ff00",
        "BULLISH": "#90ee90",
        "NEUTRAL": "#ffff00",
        "BEARISH": "#ffb6c6",
        "STRONG BEARISH": "#ff0000",
    }.get(data["overall_bias"], "#ffffff")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hedge Fund - Multi-TF Analysis</title>
        <style>
            body {{
                font-family: 'Courier New', monospace;
                background: #1a1a1a;
                color: #00ff00;
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #00ff00;
                padding-bottom: 15px;
            }}
            .symbol {{
                font-size: 32px;
                font-weight: bold;
            }}
            .overall {{
                background: {bias_color};
                color: black;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
                font-size: 24px;
                font-weight: bold;
            }}
            .timeframes {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin: 20px 0;
            }}
            .tf-box {{
                background: #2a2a2a;
                border: 2px solid #00ff00;
                border-radius: 8px;
                padding: 15px;
            }}
            .tf-title {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #00ffff;
            }}
            .metric {{
                margin: 8px 0;
                padding: 8px;
                background: #1a1a1a;
                border-radius: 4px;
            }}
            .label {{
                color: #ffff00;
                font-weight: bold;
            }}
            .value {{
                color: #00ff00;
                margin-left: 10px;
            }}
            .probability-bar {{
                width: 100%;
                height: 20px;
                background: #333;
                border-radius: 4px;
                margin-top: 5px;
                overflow: hidden;
            }}
            .probability-fill {{
                height: 100%;
                background: linear-gradient(90deg, red, yellow, lime);
                transition: width 0.3s;
            }}
            .alignment {{
                background: #2a2a2a;
                border: 2px solid #00ffff;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                text-align: center;
            }}
            .alignment-title {{
                color: #00ffff;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .alignment-value {{
                color: #00ff00;
                font-size: 18px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="symbol">{data['symbol']}</div>
                <div>Multi-Timeframe Analysis</div>
            </div>
            
            <div class="overall">
                {data['overall_bias']}
                <div style="font-size: 14px; margin-top: 5px;">
                    Avg Probability: {data['average_probability']:.1%}
                </div>
            </div>
            
            <div class="timeframes">
    """
    
    for tf in ["1h", "4h", "1d"]:
        tf_data = data["timeframes"][tf]
        if "error" not in tf_data:
            prob = tf_data["probability"]
            prob_pct = int(prob * 100)
            
            html += f"""
                <div class="tf-box">
                    <div class="tf-title">{tf.upper()}</div>
                    <div class="metric">
                        <span class="label">Trend:</span>
                        <span class="value">{tf_data['trend'].upper()}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Probability:</span>
                        <span class="value">{prob:.1%}</span>
                        <div class="probability-bar">
                            <div class="probability-fill" style="width: {prob_pct}%;"></div>
                        </div>
                    </div>
                    <div class="metric">
                        <span class="label">Confidence:</span>
                        <span class="value">{tf_data['confidence']:.1%}</span>
                    </div>
                    <div class="metric">
                        <span class="label">RSI:</span>
                        <span class="value">{tf_data['rsi']:.1f}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Risk/Reward:</span>
                        <span class="value">{tf_data['risk_reward']:.2f}</span>
                    </div>
                </div>
            """
    
    html += """
            </div>
            
            <div class="alignment">
                <div class="alignment-title">ALIGNMENT</div>
                <div class="alignment-value">""" + data['alignment'] + """</div>
                <div style="color: #666; margin-top: 5px;">
                    Strength: """ + str(int(data['alignment_strength'] * 100)) + """%
                </div>
            </div>
            
            <div class="footer">
                Hedge Fund Multi-TF Analysis | Real-time data
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
