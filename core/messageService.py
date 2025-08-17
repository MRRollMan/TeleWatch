from collections import defaultdict
from typing import TYPE_CHECKING

from telethon.tl.patched import Message
from database.models import Message as DBMessage
from telethon.tl.types import UpdateDeleteMessages, MessageMediaPhoto, MessageMediaDocument
from telethon.tl.types.updates import Difference, DifferenceSlice, DifferenceEmpty
from telethon.events.album import Album
from telethon.events.newmessage import NewMessage

if TYPE_CHECKING:
    from client import Client


class MessageService:
    @staticmethod
    async def handle_message_event(client: "Client", event: Album.Event | NewMessage.Event):
        db = client.db
        user_id = await client.get_id()
        user = await db.get_user_by_id(user_id)

        if user.ignore_users & event.is_private:
            return
        if user.ignore_groups & event.is_group:
            return
        if user.ignore_channels & event.is_channel:
            return

        messages = event.messages if isinstance(event, Album.Event) else [event.message]

        if ((messages[0].media and not isinstance(messages[0].media, (MessageMediaPhoto, MessageMediaDocument)))
                or messages[0].out):
            return

        await MessageService.handle_messages(client, messages, event.text)

    @staticmethod
    async def handle_onetime_message(client: "Client", message: Message):
        user = await client.db.get_user_by_id(await client.get_id())
        try:
            file = await client.file_service.download_message_media(client, message)
        except ValueError:
            return
        chat = await client.db.get_chat_by_id(user, message.chat_id)
        caption = "🔥\n" + message.message
        await client.bot.send_file(user.forum_id, file, caption=caption, reply_to=chat.topic_id)

    @staticmethod
    async def handle_deleted_message(client: "Client", msg_ids: list[int]):
        client_id: int = await client.get_id()
        user = await client.db.get_user_by_id(client_id)

        messages: dict[int, list[DBMessage]] = defaultdict(list)

        for d_id in msg_ids:
            msg = await client.db.get_message(user, d_id)
            if msg is None:
                continue

            if msg.grouped_id:
                messages[msg.grouped_id].append(msg)
            else:
                messages[0].append(msg)

        for g_id, messages_list in messages.items():
            if g_id == 0:
                for message in messages_list:
                    if message.attachments:
                        file = (
                            await client.bot.get_messages(user.forum_id, ids=message.attachments[0].topic_message_id)
                        ).media
                        await client.bot.send_file(user.forum_id, file=file,
                                                   caption=f"🗑\n{message.text}",
                                                   reply_to=message.chat.topic_id)
                    else:
                        await client.bot.send_message(user.forum_id,
                                                      message=f"🗑\n{message.text}",
                                                      reply_to=message.chat.topic_id)
            else:
                files = []
                for message in messages_list:
                    if not message.attachments:
                        continue
                    chat_message = await client.bot.get_messages(user.forum_id,
                                                                 ids=message.attachments[0].topic_message_id)
                    files.append(chat_message.media)
                if not files:
                    continue
                await client.bot.send_file(user.forum_id, file=files,
                                           caption=f"🗑\n{messages_list[0].text}",
                                           reply_to=messages_list[0].chat.topic_id)

    @staticmethod
    async def handle_messages(client: "Client", messages: list[Message], caption: str | None = None):
        user_id = await client.get_id()
        user = await client.db.get_user_by_id(user_id)

        async with client.lock:
            if (chat := await client.db.get_chat_by_id(user, messages[0].chat_id)) is None:
                chat = await client.client_service.create_chat(client, messages[0].chat_id, user, client.bot)

        if chat.blacklisted:
            return

        messages_obj = []
        for message in messages:
            if message.media and message.media.ttl_seconds:
                await MessageService.handle_onetime_message(client, message)
                return

            async with client.lock:
                if not (msg := await client.db.get_message(user, message.id)):
                    msg = await client.db.add_message(user, chat, message.id, message.message,
                                                      int(message.date.timestamp()), message.grouped_id
                                                      )
            messages_obj.append(msg)

        if messages[0].media:
            bot = client.bot
            bot_obj = await client.db.get_bot(await bot.get_id())
            files = [await client.file_service.download_message_media(client, message) for message in messages]
            files = files[0] if len(files) == 1 else files
            send_messages = await bot.send_file(user.forum_id, files, reply_to=user.files_topic_id, caption=caption)
            if isinstance(send_messages, Message):
                send_messages = [send_messages]

            for send_message, message_obj in zip(send_messages, messages_obj):
                await client.db.add_attachment(bot_obj, message_obj, send_message.id, '')


    @staticmethod
    async def handle_difference(client: "Client"):
        state = client.session.get_update_state(0)
        if not state:
            return
        diff = await client.get_difference(state)

        if isinstance(diff, DifferenceEmpty):
            return

        new_messages = list(filter(lambda m: not m.out, diff.new_messages))
        events = MessageService.parse_messages_to_events(new_messages)
        for event in events:
            await MessageService.handle_message_event(client, event)

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

    @staticmethod
    def parse_messages_to_events(messages: list[Message]) -> list[Album.Event | NewMessage.Event]:
        events = []
        grouped = defaultdict(list)
        for message in messages:
            if message.grouped_id:
                grouped[message.grouped_id].append(message)
            else:
                events.append(NewMessage.Event(message))

        events.extend(Album.Event(msgs) for msgs in grouped.values())

        return sorted(events, key=lambda e: e.message.id if isinstance(e, NewMessage.Event) else e.messages[0].id)
