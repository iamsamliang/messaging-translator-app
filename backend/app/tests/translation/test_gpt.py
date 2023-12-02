import pytest
from devtools import debug

from app.translation.gpt import translate


@pytest.mark.anyio
async def test_translate() -> None:
    text_input = "hey can you fix the error in the code? Then push it to Github."
    result = await translate(
        sender_id=1,
        text_input=text_input,
        target_language="Mandarin",
        chat_history=[],
    )

    assert result
    assert type(result) == str
    assert result != text_input
    debug(result.strip())
