from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.api.dependencies import get_db
from app.models import User
from app.utils.cron import repeat_every


@repeat_every(seconds=settings.UNVERIFIED_USERS_DBCLEANUP_SECS)
async def delete_expired_unverified_users() -> None:
    async for db in get_db():
        cutoff_time = datetime.utcnow() - timedelta(
            hours=settings.ACCOUNT_VERIFICATION_TOKEN_EXPIRE_HOURS
        )

        try:
            # batch deletion query
            delete_query = delete(User).where(
                User.is_verified == False, User.created_at < cutoff_time
            )

            await db.execute(delete_query)
            await db.commit()
        except IntegrityError:
            await db.rollback()
