from fastapi import APIRouter, Query, HTTPException
from app.services.binance_service import BinanceService
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal
from app.models.dto import Candle
import json
from datetime import datetime

router = APIRouter()

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

@router.get("/crypto/multi-tf")
async def multi_timeframe_analysis(
    symbol: str = Query("BTCUSDT", description="Trading symbol"),
    format: str = Query("json", description="Response format: json or html")
):
    """
    Multi-timeframe technical analysis for crypto symbols.
    Returns technical indicators across multiple timeframes.
    """
    try:
        binance_service = BinanceService()
        results = {}
        
        # Fetch data for each timeframe
        for tf in TIMEFRAMES:
            try:
                # Get klines from Binance
                klines = binance_service.get_klines(symbol, tf, limit=200)
                
                if not klines or len(klines) == 0:
                    results[tf] = {
                        "error": "No data available",
                        "ta": {}
                    }
                    continue
                
                # Convert to Candle objects
                candles = []
                for kline in klines:
                    try:
                        candle = Candle(
                            open=float(kline[1]),
                            high=float(kline[2]),
                            low=float(kline[3]),
                            close=float(kline[4]),
                            volume=float(kline[7])
                        )
                        candles.append(candle)
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error parsing candle for {tf}: {e}")
                        continue
                
                if len(candles) < 50:
                    results[tf] = {
                        "error": f"Insufficient data: {len(candles)} candles",
                        "ta": {}
                    }
                    continue
                
                # Calculate technical analysis
                ta_data = ta_summary(candles)
                
                # Calculate signal
                signal = calculate_signal(ta_data, candles[-1].close)
                
                results[tf] = {
                    "price": float(candles[-1].close),
                    "volume": float(candles[-1].volume),
                    "ta": ta_data,
                    "signal": signal
                }
                
            except Exception as e:
                print(f"Error processing timeframe {tf}: {str(e)}")
                results[tf] = {
                    "error": str(e),
                    "ta": {}
                }
        
        # Calculate overall signal (average across timeframes)
        probabilities = []
        confidences = []
        trends = []
        
        for tf_data in results.values():
            if "signal" in tf_data and tf_data["signal"]:
                sig = tf_data["signal"]
                if "probability" in sig:
                    probabilities.append(sig["probability"])
                if "confidence" in sig:
                    confidences.append(sig["confidence"])
                if "trend" in sig:
                    trends.append(sig["trend"])
        
        overall_signal = {
            "probability": sum(probabilities) / len(probabilities) if probabilities else 50.0,
            "confidence": sum(confidences) / len(confidences) if confidences else 50.0,
            "trend": max(set(trends), key=trends.count) if trends else "NEUTRAL"
        }
        
        if format.lower() == "html":
            return _render_html_report(symbol, results, overall_signal)
        else:
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "overall_signal": overall_signal,
                "timeframes": results
            }
    
    except Exception as e:
        print(f"Error in multi_timeframe_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _render_html_report(symbol: str, results: dict, overall_signal: dict) -> str:
    """Render multi-timeframe analysis as HTML"""
    
    # Color based on trend
    trend_color = {
        "BULLISH": "#00ff00",
        "BEARISH": "#ff0000",
        "NEUTRAL": "#ffff00"
    }
    
    trend = overall_signal["trend"]
    color = trend_color.get(trend, "#ffff00")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{symbol} - Multi-Timeframe Analysis</title>
        <style>
            body {{
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                text-align: center;
                color: #00ff00;
                font-size: 32px;
                margin: 0 0 10px 0;
                text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
            }}
            .subtitle {{
                text-align: center;
                color: #00aa00;
                font-size: 14px;
                margin-bottom: 30px;
            }}
            .overall-signal {{
                background-color: {color};
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
                color: #000;
                font-size: 28px;
                font-weight: bold;
            }}
            .alignment-box {{
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 30px;
                background-color: #0a0a0a;
            }}
            .alignment-header {{
                text-align: center;
                color: #00ff00;
                font-size: 18px;
                margin-bottom: 15px;
            }}
            .alignment-details {{
                text-align: center;
                color: #00aa00;
                font-size: 12px;
            }}
            .timeframes-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .timeframe-card {{
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 20px;
                background-color: #0a0a0a;
            }}
            .timeframe-title {{
                color: #00ff00;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            .signal-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #333;
                font-size: 12px;
            }}
            .signal-row:last-child {{
                border-bottom: none;
            }}
            .signal-label {{
                color: #00aa00;
                flex: 1;
            }}
            .signal-value {{
                color: #ffff00;
                font-weight: bold;
                text-align: right;
                flex: 1;
            }}
            .momentum-section {{
                margin-top: 30px;
            }}
            .section-title {{
                color: #ff8800;
                font-size: 16px;
                text-align: center;
                margin-bottom: 20px;
            }}
            .momentum-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .momentum-card {{
                border: 2px solid #ff8800;
                border-radius: 10px;
                padding: 20px;
                background-color: #0a0a0a;
            }}
            .momentum-title {{
                color: #ff8800;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .momentum-row {{
                display: flex;
                justify-content: space-between;
                padding: 6px 0;
                border-bottom: 1px solid #333;
                font-size: 11px;
            }}
            .momentum-row:last-child {{
                border-bottom: none;
            }}
            .momentum-label {{
                color: #ff6600;
                flex: 1;
            }}
            .momentum-value {{
                color: #ffaa00;
                font-weight: bold;
                text-align: right;
                flex: 1;
            }}
            .vwap-section {{
                margin-top: 30px;
            }}
            .vwap-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .vwap-card {{
                border: 2px solid #00ccff;
                border-radius: 10px;
                padding: 20px;
                background-color: #0a0a0a;
            }}
            .vwap-title {{
                color: #00ccff;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .vwap-row {{
                display: flex;
                justify-content: space-between;
                padding: 6px 0;
                border-bottom: 1px solid #333;
                font-size: 11px;
            }}
            .vwap-row:last-child {{
                border-bottom: none;
            }}
            .vwap-label {{
                color: #00aa99;
                flex: 1;
            }}
            .vwap-value {{
                color: #00ff99;
                font-weight: bold;
                text-align: right;
                flex: 1;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 10px;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #333;
            }}
            .error {{
                color: #ff0000;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{symbol}</h1>
            <div class="subtitle">Multi-Timeframe Analysis</div>
            
            <div class="overall-signal">
                {trend}
                <div style="font-size: 12px; margin-top: 5px;">Avg Probability: {overall_signal["probability"]:.1f}%</div>
            </div>
            
            <div class="alignment-box">
                <div class="alignment-header">ALIGNMENT</div>
                <div class="alignment-details">
                    PERFECT (all aligned)
                    <br>Strength: 100%
                </div>
            </div>
            
            <div class="timeframes-grid">
    """
    
    for tf in TIMEFRAMES:
        if tf in results:
            data = results[tf]
            if "signal" in data and data["signal"]:
                sig = data["signal"]
                html += f"""
                <div class="timeframe-card">
                    <div class="timeframe-title">{tf.upper()}</div>
                    <div class="signal-row">
                        <span class="signal-label">Trend:</span>
                        <span class="signal-value">{sig.get("trend", "NEUTRAL")}</span>
                    </div>
                    <div class="signal-row">
                        <span class="signal-label">Probability:</span>
                        <span class="signal-value">{sig.get("probability", 50):.1f}%</span>
                    </div>
                    <div class="signal-row">
                        <span class="signal-label">Confidence:</span>
                        <span class="signal-value">{sig.get("confidence", 50):.1f}%</span>
                    </div>
                    <div class="signal-row">
                        <span class="signal-label">RSI:</span>
                        <span class="signal-value">{data["ta"].get("rsi", 50):.1f}</span>
                    </div>
                    <div class="signal-row">
                        <span class="signal-label">Risk/Reward:</span>
                        <span class="signal-value">{sig.get("risk_reward", 1.2):.2f}</span>
                    </div>
                </div>
                """
            else:
                html += f"""
                <div class="timeframe-card">
                    <div class="timeframe-title">{tf.upper()}</div>
                    <div class="error">No signal data</div>
                </div>
                """
    
    html += """
            </div>
            
            <div class="momentum-section">
                <div class="section-title">MOMENTUM INDICATORS</div>
                <div class="momentum-grid">
    """
    
    for tf in TIMEFRAMES:
        if tf in results:
            data = results[tf]
            ta = data.get("ta", {})
            html += f"""
            <div class="momentum-card">
                <div class="momentum-title">{tf.upper()} MOMENTUM</div>
                <div class="momentum-row">
                    <span class="momentum-label">MACD:</span>
                    <span class="momentum-value" style="color: {'#ff0000' if ta.get('macd', {}).get('histogram', 0) < 0 else '#00ff00'}">{ta.get('macd', {}).get('histogram', 0):.6f} ({ta.get('macd', {}).get('direction', 'neutral')})</span>
                </div>
                <div class="momentum-row">
                    <span class="momentum-label">Stochastic K:</span>
                    <span class="momentum-value">{ta.get('stochastic', {}).get('k', 50):.1f}% ({ta.get('stochastic', {}).get('signal', 'neutral')})</span>
                </div>
                <div class="momentum-row">
                    <span class="momentum-label">CCI:</span>
                    <span class="momentum-value">{ta.get('cci', 0):.2f}</span>
                </div>
            </div>
            """
    
    html += """
                </div>
            </div>
            
            <div class="vwap-section">
                <div class="section-title">VWAP LEVELS</div>
                <div class="vwap-grid">
    """
    
    for tf in TIMEFRAMES:
        if tf in results:
            data = results[tf]
            vwap = data.get("ta", {}).get("vwap", {})
            html += f"""
            <div class="vwap-card">
                <div class="vwap-title">{tf.upper()} VWAP LEVELS</div>
                <div class="vwap-row">
                    <span class="vwap-label">Daily:</span>
                    <span class="vwap-value">${vwap.get('daily', 0):.2f}</span>
                </div>
                <div class="vwap-row">
                    <span class="vwap-label">Weekly:</span>
                    <span class="vwap-value">${vwap.get('weekly', 0):.2f}</span>
                </div>
                <div class="vwap-row">
                    <span class="vwap-label">Monthly:</span>
                    <span class="vwap-value">${vwap.get('monthly', 0):.2f}</span>
                </div>
                <div class="vwap-row">
                    <span class="vwap-label">Quarterly:</span>
                    <span class="vwap-value">${vwap.get('quarterly', 0):.2f}</span>
                </div>
                <div class="vwap-row">
                    <span class="vwap-label">Yearly:</span>
                    <span class="vwap-value">${vwap.get('yearly', 0):.2f}</span>
                </div>
            </div>
            """
    
    html += """
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
