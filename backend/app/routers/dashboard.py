from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middlewares.auth import get_current_user
from app.services.trial_service import get_trial_stats

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/trial-stats")
async def get_trial_stats_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Dashboard API: Returns trial usage and stats for the authenticated user.
    """
    stats = await get_trial_stats(current_user.id, db)
    return stats