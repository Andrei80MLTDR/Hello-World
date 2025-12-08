from fastapi import APIRouter
from typing import List
from app.models.dto import EconEvent

router = APIRouter(prefix="/econ", tags=["economic"])

@router.get("/calendar", response_model=List[EconEvent])
async def get_calendar():
    return []
