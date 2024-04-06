from app.models import group_member_association
from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession


async def associate_users_to_convo(
    *, db: AsyncSession, member_associations: list[dict[str, int]]
) -> None:
    await db.execute(
        insert(group_member_association),
        member_associations,
    )


async def remove_user_from_convo(
    *, db: AsyncSession, user_id: int, convo_id: int
) -> None:
    await db.execute(
        delete(group_member_association).where(
            group_member_association.c.user_id == user_id,
            group_member_association.c.conversation_id == convo_id,
        )
    )
