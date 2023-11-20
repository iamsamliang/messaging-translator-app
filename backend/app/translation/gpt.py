import openai


async def translate(
    *,
    sender_id: int,
    text_input: str,
    target_language: str,
    chat_history: list[tuple],
):
    # User {message.sender_id}: {translation.text}
    # User ....

    PROMPT_MSGS = [
        {
            "role": "system",
            "content": "You are a messages translator. You're given the chat history.",
        },
    ]

    for message in chat_history:
        PROMPT_MSGS.append(
            {"role": "user", "name": f"User {message[0]}", "content": {message[1]}}
        )

    PROMPT_MSGS.append(
        {
            "role": "user",
            "name": f"User {sender_id}",
            "content": f"User {sender_id} sent '{text_input}'. Translate it to {target_language}.",
        }
    )

    # prompt = """You're given the chat history here
    # """

    # prompt += (
    #     f"\nUser {sender_id} sent '{text_input}'. Translate it to {target_language}.\n"
    # )

    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=PROMPT_MSGS,
    )

    return response.choices[0].message.content
