from typing import TYPE_CHECKING

from telethon.tl.patched import Message
from telethon.tl.types import UpdateDeleteMessages, MessageMediaPhoto, MessageMediaDocument
from telethon.tl.types.updates import Difference, DifferenceSlice, DifferenceEmpty

from core.botService import BotService
from core.fileService import FileService

if TYPE_CHECKING:
    from client import Client


class MessageService:
    @staticmethod
    async def handle_onetime_message(client: "Client", message: Message):
        user = await client.db.get_user_by_id(await client.get_id())
        try:
            file = await FileService.download_message_media(client, message)
        except ValueError:
            return
        chat = await client.db.get_chat_by_id(user, message.chat_id)
        caption = "🔥\n" + message.message
        await client.bot.send_file(user.forum_id, file, caption=caption, reply_to=chat.topic_id)

    @staticmethod
    async def handle_deleted_message(client: "Client", msg_ids: list[int]):
        client_id: int = await client.get_id()
        user = await client.db.get_user_by_id(client_id)

        for d_id in msg_ids:
            msg = await client.db.get_message(user, d_id)
            if msg is None:
                continue
            if msg.attachments:
                media = (await client.bot.get_messages(user.forum_id, ids=msg.attachments[0].topic_message_id)).media
                await client.bot.send_file(user.forum_id, file=media,
                                           caption=f"🗑\n{msg.text}",
                                           reply_to=msg.chat.topic_id)
            else:
                await client.bot.send_message(user.forum_id,
                                              message=f"🗑\n{msg.text}",
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

        async with client.lock:
            if (chat := await client.db.get_chat_by_id(user, message.chat_id)) is None:
                chat = await BotService.create_chat(client, message.chat_id, user, client.bot)

        if chat.blacklisted:
            return
        if message.media and not isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
            return

        if message.media and message.media.ttl_seconds:
            await MessageService.handle_onetime_message(client, message)
            return

        async with client.lock:
            if not (msg := await db.get_message(user, message.id)):
                msg = await db.add_message(user,
                                           chat,
                                           message.id,
                                           message.message,
                                           int(message.date.timestamp()),
                                           message.grouped_id
                                           )
        if message.media:
            bot = client.bot
            bot_obj = await db.get_bot(await bot.get_id())
            file = await FileService.download_message_media(client, message)
            send_msg = await bot.send_file(user.forum_id, file, reply_to=user.files_topic_id)
            await db.add_attachment(bot_obj, msg, send_msg.id, '')

    @staticmethod
    async def handle_difference(client: "Client"):
        state = client.session.get_update_state(0)
        if not state:
            return
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
