import openai


async def translate(
    *,
    sender_id: int,
    text_input: str,
    target_language: str,
    chat_history: list[tuple[int, str]],
) -> str | None:
    # User {message.sender_id}: {translation.text}
    # User ....

    PROMPT_MSGS = [
        {
            "role": "system",
            "content": "Your job is to translate messages that users text to each other. You're given the chat history as context to help translating and who sent the newest message. Only return the translation of that message",
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
            "content": f"User {sender_id} sent '{text_input}'. Translate it to {target_language}.",
        }
    )

    # prompt = """You're given the chat history here
    # """

    # prompt += (
    #     f"\nUser {sender_id} sent '{text_input}'. Translate it to {target_language}.\n"
    # )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=PROMPT_MSGS,  # type: ignore
    )

    return response.choices[0].message.content
