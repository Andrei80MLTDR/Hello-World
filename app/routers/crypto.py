from fastapi import APIRouter
from app.models.dto import PriceResponse

router = APIRouter(prefix="/crypto", tags=["crypto"])

@router.get("/price", response_model=PriceResponse)
async def get_price(symbol: str = "BTCUSDT"):
    # Temporar, doar placeholder; vom conecta Binance/CoinGecko
    return PriceResponse(symbol=symbol, price=0.0)
