from app.exceptions import OpenAIAuthenticationException
import openai


async def translate(
    *,
    sender_id: int,
    text_input: str,
    target_language: str,
    chat_history: list[tuple[int, str]],
    api_key: str,
) -> str | None:
    # User {message.sender_id}: {translation.text}
    # User ....

    PROMPT_MSGS = [
        {
            "role": "system",
            "content": "Your job is to translate messages that users text to each other. You're given the chat history as context and the sender of the newest message. Only return the translation of that message",
        },
    ]

    # messages are all in the language of the sender for better accuracy
    for message in chat_history:
        PROMPT_MSGS.append(
            {"role": "user", "name": f"User_{message[0]}", "content": message[1]}
        )

    PROMPT_MSGS.append(
        {
            "role": "user",
            "name": f"User_{sender_id}",
            "content": f"""Translate the following text sent by user {sender_id} into {target_language}. Ensure the punctuation remains EXACTLY the SAME as in the ORIGINAL TEXT. DO NOT ADD EXTRA QUOTES to the translation if there were no quotes in the original input.
            
            {text_input}""",
        }
    )

    # prompt = """You're given the chat history here
    # """

    # prompt += (
    #     f"\nUser {sender_id} sent '{text_input}'. Translate it to {target_language}.\n"
    # )

    # print(f"In GPT Translation Function. This is the prompt: {PROMPT_MSGS}")

    # whitespace will already be stripped. The strippping is necessary
    if not api_key:
        raise OpenAIAuthenticationException()

    openai.api_key = api_key

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=PROMPT_MSGS,  # type: ignore
    )

    return response.choices[0].message.content
