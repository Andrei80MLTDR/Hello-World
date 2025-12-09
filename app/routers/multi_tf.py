from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse

from app.services.binance_service import BinanceService
from app.services.ta_engine import ta_summary
from app.services.signal_engine import calculate_signal

router = APIRouter(prefix="/crypto", tags=["crypto"])

binance_service = BinanceService()


TIMEFRAMES = {
    "1m": {"interval": "1m", "limit": 200},
    "5m": {"interval": "5m", "limit": 200},
    "15m": {"interval": "15m", "limit": 200},
    "1h": {"interval": "1h", "limit": 200},
    "4h": {"interval": "4h", "limit": 200},
    "1d": {"interval": "1d", "limit": 200},
}


def build_timeframe_data(symbol: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    for tf_name, cfg in TIMEFRAMES.items():
        try:
            candles = binance_service.get_candles(
                symbol=symbol,
                interval=cfg["interval"],
                limit=cfg["limit"],
            )
            if not candles:
                result[tf_name] = {
                    "error": "Insufficient data: 0 candles",
                    "ta": {},
                }
                continue

            ta = ta_summary(candles)
            signal = calculate_signal(candles, ta)

            result[tf_name] = {
                "candles": [candle.dict() for candle in candles],
                "ta": ta,
                "signal": signal,
            }
        except Exception as e:
            result[tf_name] = {
                "error": str(e),
                "ta": {},
            }

    return result


def render_html(symbol: str, overall: Dict[str, Any], tfs: Dict[str, Any]) -> str:
    # Simplu: UI tip „terminal” cu timeframes + indicatori de bază
    timestamp = overall.get("timestamp", datetime.utcnow().isoformat())
    prob = overall.get("probability", 50.0)
    conf = overall.get("confidence", 50.0)
    trend = overall.get("trend", "NEUTRAL")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>{symbol} - Multi-Timeframe Analysis</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                background-color: #141a1f;
                color: #00ff00;
                font-family: "Courier New", monospace;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                text-align: center;
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .subtitle {{
                text-align: center;
                color: #888;
                margin-bottom: 20px;
            }}
            .overall-signal {{
                border: 2px solid #00ff00;
                padding: 15px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
            }}
            .overall-item {{
                margin: 5px 10px;
                font-size: 16px;
            }}
            .timeframes-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 12px;
            }}
            .timeframe-card {{
                border: 1px solid #00ff00;
                padding: 10px;
                background-color: #111;
                font-size: 13px;
            }}
            .tf-title {{
                font-weight: bold;
                margin-bottom: 5px;
                font-size: 14px;
            }}
            .error {{
                color: #ff6666;
                font-size: 12px;
            }}
            .footer {{
                margin-top: 25px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{symbol} Multi-Timeframe Terminal</h1>
            <div class="subtitle">Generated at {timestamp}</div>

            <div class="overall-signal">
                <div class="overall-item">Trend: {trend}</div>
                <div class="overall-item">Prob: {prob:.1f}%</div>
                <div class="overall-item">Confidence: {conf:.1f}%</div>
            </div>

            <div class="timeframes-grid">
    """

    for tf_name, data in tfs.items():
        html += f'<div class="timeframe-card">'
        html += f'<div class="tf-title">{tf_name.upper()}</div>'

        if "error" in data and data["error"]:
            html += f'<div class="error">{data["error"]}</div>'
        else:
            sig = data.get("signal", {}) or {}
            ta = data.get("ta", {}) or {}
            dir_ = sig.get("direction", "neutral")
            score = sig.get("score", 0)

            html += f'<div>Signal: {dir_.upper()} (score {score:.1f})</div>'
            if "ema_fast" in ta and "ema_slow" in ta:
                html += f'<div>EMA Fast: {ta["ema_fast"]:.2f}</div>'
                html += f'<div>EMA Slow: {ta["ema_slow"]:.2f}</div>'
            if "rsi" in ta:
                html += f'<div>RSI: {ta["rsi"]:.1f}</div>'

        html += "</div>"

    html += """
            </div>
            <div class="footer">
                Hedge Fund Multi-TF Analysis | Real-time data
            </div>
        </div>
    </body>
    </html>
    """

    return html


@router.get("/multi-tf")
async def crypto_multi_tf(
    symbol: str = Query("BTCUSDT"),
    format: str = Query("json", regex="^(json|html)$"),
) -> Any:
    """
    Multi-timeframe analysis endpoint.
    - format=json (default): obiect JSON
    - format=html: UI terminal în browser
    """
    try:
        timeframes_data = build_timeframe_data(symbol)

        # overall signal simplu: media scorurilor
        scores = []
        for data in timeframes_data.values():
            sig = data.get("signal")
            if sig and isinstance(sig, dict):
                s = sig.get("score")
                if isinstance(s, (int, float)):
                    scores.append(s)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        trend = "NEUTRAL"
        if avg_score > 0.5:
            trend = "BULLISH"
        elif avg_score < -0.5:
            trend = "BEARISH"

        overall = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "probability": 50.0 + avg_score * 10,
            "confidence": min(100.0, max(0.0, len(scores) * 10.0)),
            "trend": trend,
        }

        if format == "html":
            html = render_html(symbol, overall, timeframes_data)
            return HTMLResponse(content=html, status_code=200)

        return {
            "symbol": symbol,
            "timestamp": overall["timestamp"],
            "overall_signal": overall,
            "timeframes": timeframes_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
