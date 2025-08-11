from typing import TYPE_CHECKING

from telethon.tl.patched import Message
from telethon.tl.types import UpdateDeleteMessages
from telethon.tl.types.updates import Difference, DifferenceSlice, DifferenceEmpty

from core.fileService import FileService

if TYPE_CHECKING:
    from client import Client


class MessageService:
    @staticmethod
    async def handle_onetime_message(client: "Client", message: Message):
        user = await client.db.get_user_by_id(await client.get_id())
        file = await FileService.download_message_media(client, message)
        chat = await client.db.get_chat_by_id(user, message.chat_id)
        caption = "🔥\n" + message.message
        await client.bot.send_file(user.forum_id, file, caption=caption, reply_to=chat.topic_id)

    @staticmethod
    async def handle_deleted_message(client: "Client", msg_ids: list[int]):
        client_id: int = await client.get_id()
        user = await client.db.get_user_by_id(client_id)

        for d_id in msg_ids:
            msg = await client.db.get_message(user, d_id)
            if msg is not None:
                await client.bot.send_message(user.forum_id,
                                              f"🗑: \n{msg.text}",
                                              reply_to=msg.chat.topic_id)

    @staticmethod
    async def handle_message(client: "Client", message: Message):
        db = client.db
        user_id = await client.get_id()
        user = await db.get_user_by_id(user_id)
        if user.ignore_users & message.is_private:
            return
        if user.ignore_groups & message.is_group:
            return
        if user.ignore_channels & message.is_channel:
            return

        chat_id = message.chat_id
        chat_obj = await client.get_entity(chat_id)
        fullname = f"{chat_obj.first_name} {chat_obj.last_name}" if chat_obj.last_name is not None else chat_obj.first_name
        async with client.lock:
            if not await db.has_chat(user, chat_id):
                topic_id = await client.bot.create_topic(user.forum_id, fullname)
                chat = (await db.add_chat(user, chat_id, topic_id))[0]
            else:
                chat = await db.get_chat_by_id(user, chat_id)

        if message.media and message.media.ttl_seconds:
            await MessageService.handle_onetime_message(client, message)
        else:
            await db.add_message(user, chat, message.id, message.message, int(message.date.timestamp()))

    @staticmethod
    async def handle_difference(client: "Client"):
        state = client.session.get_update_state(0)
        diff = await client.get_difference(state)

        if isinstance(diff, DifferenceEmpty):
            return

        for message in diff.new_messages:
            if message.out:
                continue
            await MessageService.handle_message(client, message)

        for update in diff.other_updates:
            if isinstance(update, UpdateDeleteMessages):
                await MessageService.handle_deleted_message(client, update.messages)

        if isinstance(diff, Difference):
            new_state = diff.state
            client.session.set_update_state(0, new_state)
        elif isinstance(diff, DifferenceSlice):
            new_state = diff.intermediate_state
            client.session.set_update_state(0, new_state)
            await MessageService.handle_difference(client)
