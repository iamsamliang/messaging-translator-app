from app import crud
from app.tests.utils.convo import create_random_convo
from app.tests.utils.user import create_random_user_stochastic
from app.tests.utils.utils import random_string
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app


@pytest.mark.anyio
async def test_create_messages(db: AsyncSession, faker: Faker) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        random_user1 = await create_random_user_stochastic(db=db, faker=faker)
        random_user2 = await create_random_user_stochastic(
            db=db, faker=faker, target_lang="chinese"
        )
        await db.commit()

        convo_json = {
            "conversation_name": random_string(10),
            "user_ids": [{"email": random_user1.email}, {"email": random_user2.email}],
        }

        response = await ac.post("/conversations", json=convo_json)

        assert response.status_code == 201

        get_new_convo = await crud.conversation.get(db=db, id=response.json()["id"])

        assert get_new_convo

        response = await ac.post(
            "/messages",
            json={
                "conversation_id": get_new_convo.id,
                "sender_id": random_user1.id,
                "original_text": "Hello world",
                "orig_language": "English",
            },
        )

        assert response.status_code == 201
        assert (
            response.headers["Location"]
            == f"/messages/{response.json()['conversation_id']}/{response.json()['sender_id']}"
        )

        get_message = await crud.message.get(db=db, id=response.json()["id"])

        created_msg = response.json()

        assert get_message
        assert get_message.original_text == created_msg["original_text"]
        assert (
            jsonable_encoder(get_message, exclude={"sent_at", "received_at"})
            == created_msg
        )

        # when we create a message, we need to check that is got added to user_1 sent messages
        # got added to user_2 received messages
        # got added to the conversation's messages
        # got associated with translations

        assert (await get_message.awaitable_attrs.conversation).id == get_new_convo.id
        assert len((await get_message.awaitable_attrs.translations)) == 1

        # migiht need refresh here
        assert (await get_new_convo.awaitable_attrs.messages)[0].id == get_message.id

        assert (await random_user1.awaitable_attrs.messages_sent)[
            0
        ].id == get_message.id

        assert (await random_user2.awaitable_attrs.messages_received)[
            0
        ].language == "chinese"
        assert (await random_user2.awaitable_attrs.messages_received)[
            0
        ].message_id == get_message.id
