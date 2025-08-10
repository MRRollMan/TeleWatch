from telethon import events
from telethon.tl.types import UpdateDeleteChannelMessages

from database import Database


#TODO: Refactor this to use a more structured event system
@events.register(events.MessageDeleted)
async def message_deleted_handler(event: events.messagedeleted.MessageDeleted.Event):
    db = Database()
    client_id: int = await event.client.get_id()
    user = await db.get_user_by_id(client_id)

    for d_id in event.deleted_ids:
        if isinstance(event.original_update, UpdateDeleteChannelMessages):
            chat = await db.get_chat_by_id(user, event.chat_id)
            msg = await db.get_message_by_chat(user, chat, d_id)
            print(msg, "1")
        else:
            msg = await db.get_message(user, d_id)
            print(msg, "2")
        if msg is not None:
            await event.client.bot.send_message(user.forum_id,
                                                f"🗑: \n{msg.text}",
                                                reply_to=msg.chat.topic_id)
