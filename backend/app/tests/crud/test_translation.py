import pytest

from faker import Faker

from app import crud
from app.schemas import TranslationCreate
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.utils.message import create_random_message
from app.tests.utils.user import create_random_user_stochastic


@pytest.mark.anyio
async def test_create_get_translation(db: AsyncSession, faker: Faker) -> None:
    target_user = await create_random_user_stochastic(db=db, faker=faker)
    sender_msg = await create_random_message(
        db=db, faker=faker, text="my name is Sam", language="english"
    )
    await db.flush()

    translation_schema = TranslationCreate(
        translation="me llamo Sam",
        language="spanish",
        target_user_id=target_user.id,
        message_id=sender_msg.id,
    )

    created_translation = await crud.translation.create(
        db=db, obj_in=translation_schema
    )
    await db.commit()

    get_translation = await crud.translation.get(db=db, id=created_translation.id)
    assert get_translation
    assert get_translation.translation == created_translation.translation
    assert jsonable_encoder(get_translation) == jsonable_encoder(created_translation)
    assert (
        await get_translation.awaitable_attrs.message
    ).original_text == sender_msg.original_text
    assert (await get_translation.awaitable_attrs.user).email == target_user.email


@pytest.mark.anyio
async def test_delete_translation(db: AsyncSession, faker: Faker) -> None:
    target_user = await create_random_user_stochastic(db=db, faker=faker)
    sender_msg = await create_random_message(
        db=db, faker=faker, text="my name is Sam", language="english"
    )
    await db.flush()

    translation_schema = TranslationCreate(
        translation="me llamo Sam",
        language="spanish",
        target_user_id=target_user.id,
        message_id=sender_msg.id,
    )

    created_translation = await crud.translation.create(
        db=db, obj_in=translation_schema
    )
    await db.commit()
    translation_id = created_translation.id

    await crud.message.delete(db=db, id=translation_id)
    await db.commit()
    assert await crud.message.get(db=db, id=translation_id) is None


# Update not used on Translation so not testing
