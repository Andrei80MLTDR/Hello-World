from fastapi import APIRouter, HTTPException
from app.models.dto import PriceResponse
from app.services.binance_client import get_binance_price
# from app.services.coingecko_client import get_coingecko_price  # pentru fallback ulterior

router = APIRouter(prefix="/crypto", tags=["crypto"])

@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str = "BTCUSDT"):
    try:
        price = await get_binance_price(symbol)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Binance price error: {e}")
    return PriceResponse(symbol=symbol, price=price)
