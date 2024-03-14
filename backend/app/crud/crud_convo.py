import json

from typing import Sequence
from app.core.config import settings
from app.schemas.responses import MembersOut
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.models import Conversation, User, group_member_association
from app.schemas import (
    ConversationCreateDB,
    ConversationUpdate,
    Method,
    GetMembersResponse,
)
from app.utils.aws import (
    delete_object,
    generate_presigned_get_url,
    get_cached_presigned_obj,
    CacheMethod,
)
from .base import CRUDBase


class CRUDConversation(
    CRUDBase[Conversation, ConversationCreateDB, ConversationUpdate]
):
    async def create(
        self, db: AsyncSession, *, obj_in: ConversationCreateDB
    ) -> Conversation:
        """When we create a conversation, we must have users that we want to add already

        Args:
            db (AsyncSession)
            convo (ConversationCreateDB)

        Returns:
            Conversation: the created Conversation object
        """
        # 1. add the new convo to the conversation table
        # 2. update group_member_assoication table to add the existing users to the new convo
        # NOTE: Check if conversation already exists
        return await super().create(db=db, obj_in=obj_in)

    async def update_users(
        self,
        db: AsyncSession,
        *,
        convo_id: int,
        users: list[User],
        method: Method,
        redis: Redis,
        sorted_curr_ids: list[int],
    ) -> Conversation | None:
        # optimized
        convo = (
            (await db.execute(select(Conversation).filter_by(id=convo_id)))
            .scalars()
            .first()
        )
        if not convo:
            return None

        if method == Method.ADD:
            members_dict = {}

            for added_user in users:
                sorted_curr_ids.append(added_user.id)

                url = None

                if added_user.profile_photo:
                    _, url = await get_cached_presigned_obj(
                        object_key=added_user.profile_photo,
                        redis_client=redis,
                        method=CacheMethod.GET,
                    )

                    if not url:
                        url = await generate_presigned_get_url(
                            bucket_name="translation-messaging-bucket",
                            object_key=added_user.profile_photo,
                            expire_in_secs=settings.S3_PRESIGNED_URL_GET_EXPIRE_SECS,
                            redis_client=redis,
                        )

                setattr(
                    added_user,
                    "presigned_url",
                    url,
                )

                members_dict[added_user.id] = MembersOut(**jsonable_encoder(added_user))

            ws_data = GetMembersResponse(
                members=members_dict,
                sorted_member_ids=sorted_curr_ids,
                gc_url=None,
            ).model_dump()

            # must go before new users subscribe to chat channel
            await redis.publish(
                f"chat_{convo_id}",
                json.dumps(
                    {
                        "type": "add_members",
                        "data": {"convo_id": convo_id, "members": ws_data},
                    }
                ),
            )

            for user in users:
                if user not in await convo.awaitable_attrs.members:  # not in group
                    (await convo.awaitable_attrs.members).append(user)

                    await redis.publish(
                        f"{user.id}",
                        json.dumps(
                            {
                                "type": "add_self",
                                "data": {
                                    "convo_id": convo_id,
                                },
                            }
                        ),
                    )
        else:
            deleted_ids = []
            convo_members = await convo.awaitable_attrs.members
            for user in users:
                if user in convo_members:  # user is in group
                    convo_members.remove(user)

                    await redis.publish(
                        f"{user.id}",
                        json.dumps(
                            {
                                "type": "delete_self",
                                "data": {
                                    "convo_id": convo_id,
                                },
                            }
                        ),
                    )

                    sorted_curr_ids.remove(user.id)
                    deleted_ids.append(user.id)

            members_remaining = len(convo_members)
            if members_remaining <= 1 and convo.is_group_chat:
                if members_remaining == 1:
                    await redis.publish(
                        f"{convo_members[0].id}",
                        json.dumps(
                            {
                                "type": "delete_self",
                                "data": {
                                    "convo_id": convo_id,
                                },
                            }
                        ),
                    )

                # delete convo and GC pic from S3
                obj_key = convo.conversation_photo

                await self.delete(db=db, id=convo_id)

                if obj_key:
                    delete_object(
                        bucket_name="translation-messaging-bucket", object_key=obj_key
                    )
            else:
                # must go after removed users unsubscribed from chat channel
                await redis.publish(
                    f"chat_{convo_id}",
                    json.dumps(
                        {
                            "type": "delete_members",
                            "data": {
                                "convo_id": convo_id,
                                "member_ids": deleted_ids,
                                "sorted_curr_ids": sorted_curr_ids,
                            },
                        }
                    ),
                )
        return convo

    async def is_user_in_conversation(
        self, db: AsyncSession, user_id: int, conversation_id: int
    ) -> bool:
        # optimized
        query = select(group_member_association).where(
            group_member_association.c.user_id == user_id,
            group_member_association.c.conversation_id == conversation_id,
        )
        result = await db.execute(query)
        return result.scalar() is not None

    async def get_members(
        self, db: AsyncSession, conversation_id: int
    ) -> Sequence[User]:
        # optimized
        query = (
            select(User)
            .join(Conversation.members)
            .where(Conversation.id == conversation_id)
        )
        result = await db.execute(query)
        return result.scalars().all()


conversation = CRUDConversation(Conversation)
