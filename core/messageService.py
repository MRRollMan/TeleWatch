from typing import TYPE_CHECKING

from telethon import events

from core.fileService import FileService

if TYPE_CHECKING:
    from client import Client


class MessageService:
    @staticmethod
    async def handle_onetime_message(client: "Client", event: events.newmessage.NewMessage.Event):
        message = event.message
        user = await client.db.get_user_by_id(await client.get_id())
        file = await FileService.download_message_media(client, message)
        chat = await client.db.get_chat_by_id(user, event.chat_id)
        caption = "🔥\n" + message.message
        await client.bot.send_file(user.forum_id, file, caption=caption, reply_to=chat.topic_id)

    @staticmethod
    async def handle_message(client: "Client", event):
        pass
