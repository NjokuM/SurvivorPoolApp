from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.results import process_gameweek_results

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/process-results/{competition_id}/{gameweek}")
async def process_results(
    competition_id: int,
    gameweek: int,
    db: AsyncSession = Depends(get_db)
):
    summary = await process_gameweek_results(
        db=db,
        competition_id=competition_id,
        gameweek=gameweek,
        allow_eliminated_to_play=True,
        apply_decrements_for_eliminated=False
    )
    return summary