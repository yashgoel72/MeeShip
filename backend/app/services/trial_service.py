from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.image import ProcessedImage

# Maximum number of free trial images per user (non-paid users)
TRIAL_UPLOAD_LIMIT = 2

async def get_trial_usage(user_id, db: AsyncSession):
    result = await db.execute(
        select(ProcessedImage)
        .where(ProcessedImage.user_id == user_id)
        .where(ProcessedImage.is_trial == True)
    )
    images = result.scalars().all()
    return len(images)

async def is_trial_upload_allowed(user_id, db: AsyncSession):
    usage = await get_trial_usage(user_id, db)
    return usage < TRIAL_UPLOAD_LIMIT

async def get_trial_stats(user_id, db: AsyncSession):
    usage = await get_trial_usage(user_id, db)
    return {
        "trial_uploads_used": usage,
        "trial_uploads_remaining": max(0, TRIAL_UPLOAD_LIMIT - usage),
        "trial_upload_limit": TRIAL_UPLOAD_LIMIT
    }