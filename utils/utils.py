TEXT_LIMIT = 4096  # Max message length
CAPTION_LIMIT = 1024  # Max caption length


async def send_chunked_message(client, text: str, entity, reply_to: int, file=None, bot=None):
    if not bot:
        bot = client.bot

    if file:
        send_message = bot.send_file(entity, file=file,
                                     caption=text[:CAPTION_LIMIT],
                                     reply_to=reply_to)
        text_limit = CAPTION_LIMIT
    else:
        send_message = client.bot.send_message(entity,
                                               message=text[:TEXT_LIMIT],
                                               reply_to=reply_to)
        text_limit = TEXT_LIMIT

    if len(text) <= text_limit:
        await send_message
    else:
        await send_message

        remaining_text = text[text_limit:]
        while remaining_text:
            remaining_text = "⬆️\n" + remaining_text
            part = remaining_text[:TEXT_LIMIT]
            remaining_text = remaining_text[TEXT_LIMIT:]
            await client.bot.send_message(entity, part, reply_to=reply_to)
