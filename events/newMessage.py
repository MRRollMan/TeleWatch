from io import BytesIO

from telethon import events
from telethon.tl.types import MessageMediaPhoto
from telethon.types import Message, PeerChannel, PeerChat

from core.messageService import MessageService
from database import Database

from client import Client

# TODO: Refactor this to use a more structured event system
@events.register(events.NewMessage(outgoing=False))
async def new_message_handler(event: events.newmessage.NewMessage.Event):
    db = Database()
    message: Message = event.message
    client: Client = event.client
    user_id = await client.get_id()
    user = await db.get_user_by_id(user_id)
    # print(event.is_private, event.is_group, event.is_channel)
    if user.ignore_users & event.is_private:
        return
    if user.ignore_groups & event.is_group:
        return
    if user.ignore_channels & event.is_channel:
        return

    chat_id = event.chat_id
    chat_obj = await client.get_entity(chat_id)
    fullname = f"{chat_obj.first_name} {chat_obj.last_name}" if chat_obj.last_name is not None else chat_obj.first_name
    if not await db.has_chat(user, chat_id):
        topic_id = await client.create_topic(user.forum_id, fullname)
        chat = (await db.add_chat(user, chat_id, topic_id))[0]
    else:
        chat = await db.get_chat_by_id(user, chat_id)

    if message.media and message.media.ttl_seconds:
        await MessageService.handle_onetime_message(client, event)
    else:
        await db.add_message(user, chat, message.id, message.message, int(message.date.timestamp()))
    # await event.client.send_message('me', 'SAVED')
