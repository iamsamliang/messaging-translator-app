import asyncio
import json

from typing import Sequence
from app.core.config import settings
from app.crud import crud_association
from app.schemas.responses import MembersOut
from app.utils.convo import generate_convo_identifier
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import aliased
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
    async def get_convo_by_identifier(
        self, *, db: AsyncSession, convo_identifier: str
    ) -> Conversation | None:
        convo = (
            (
                await db.execute(
                    select(Conversation).where(
                        Conversation.chat_identifier == convo_identifier
                    )
                )
            )
            .scalars()
            .first()
        )

        return convo

    async def get_user_convos(
        self, db: AsyncSession, *, user_id: int, offset: int, limit: int
    ) -> Sequence[Conversation]:
        # Create an alias for the conversation to use in the subquery.
        # Necessary bc the query using the subquery also operates on Conversation
        conversation_alias = aliased(Conversation)

        # Construct the subquery to select the latest 30 conversation IDs for the given user.
        # optimized
        subquery = (
            select(conversation_alias.id)
            .join(
                group_member_association,
                group_member_association.c.conversation_id == conversation_alias.id,
            )
            .where(group_member_association.c.user_id == user_id)
            .order_by(conversation_alias.latest_message_id.desc())
            .offset(offset)  # start after the `offset`'th item
            .limit(limit)  # only take `limit` number of items
            .subquery()
        )

        # Return the Conversation objects based on the subquery results.
        # optimized
        return (
            (
                await db.execute(
                    select(Conversation)
                    .join(subquery, Conversation.id == subquery.c.id)
                    .order_by(Conversation.latest_message_id.asc())
                )
            )
            .scalars()
            .all()
        )

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
            pub_messages = []
            member_associations = []

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
                            bucket_name=settings.S3_BUCKET_NAME,
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
                member_associations.append(
                    {"user_id": added_user.id, "conversation_id": convo_id}
                )
                pub_messages.append(
                    (
                        f"{added_user.id}",
                        json.dumps(
                            {
                                "type": "add_self",
                                "data": {
                                    "convo_id": convo_id,
                                },
                            }
                        ),
                    )
                )

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

            # change chat_identifer to use new list of users
            convo.chat_identifier = generate_convo_identifier(user_ids=sorted_curr_ids)

            await crud_association.associate_users_to_convo(
                db=db, member_associations=member_associations
            )
            await asyncio.gather(
                *(redis.publish(channel, message) for channel, message in pub_messages)
            )

            # batch this
            # for user in users:
            # if user not in await convo.awaitable_attrs.members:  # not in group
            #     (await convo.awaitable_attrs.members).append(user)

            #     await redis.publish(
            #         f"{user.id}",
            #         json.dumps(
            #             {
            #                 "type": "add_self",
            #                 "data": {
            #                     "convo_id": convo_id,
            #                 },
            #             }
            #         ),
            #     )
        else:
            # can only delete one user at a time
            deleted_ids = []
            convo_members = await convo.awaitable_attrs.members
            user = users[0]

            # await crud_association.remove_user_from_convo(db=db, user_id=user.id, convo_id=convo_id)
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

                # delete convo
                obj_key = convo.conversation_photo
                await self.delete(db=db, id=convo_id)

                # delete chat pic from S3 bucket
                if obj_key:
                    delete_object(
                        bucket_name=settings.S3_BUCKET_NAME, object_key=obj_key
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

                # change chat_identifer to use new list of users
                convo.chat_identifier = generate_convo_identifier(
                    user_ids=sorted_curr_ids
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
