from collections import defaultdict
from datetime import timedelta
from typing import TYPE_CHECKING
import logging

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

        if messages[0].out:
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

            msg.deleted = True
            await msg.save()

            if msg.grouped_id:
                messages[msg.grouped_id].append(msg)
            else:
                messages[0].append(msg)

        for g_id, messages_list in messages.items():
            if g_id == 0:
                for message in messages_list:
                    if message.attachment:
                        bot = client.telewatch.bots.get(message.attachment.bot.bot_id)
                        chat_message = await bot.get_messages(user.forum_id,
                                                              ids=message.attachment.topic_message_id)
                        if not isinstance(chat_message, Message):
                            continue

                        await bot.send_file(user.forum_id, file=chat_message.media,
                                            caption=f"🗑\n{message.text}",
                                            reply_to=message.chat.topic_id)
                    else:
                        await client.bot.send_message(user.forum_id,
                                                      message=f"🗑\n{message.text}",
                                                      reply_to=message.chat.topic_id)
            else:
                if not messages_list[0].attachment:
                    continue
                bot = client.telewatch.bots.get(messages_list[0].attachment.bot.bot_id)
                messages_ids = [message.attachment.topic_message_id for message in messages_list if
                                message.attachment]
                chat_messages = await bot.get_messages(user.forum_id,
                                                       ids=messages_ids)
                files = [message.media for message in chat_messages if message.media]
                if not files:
                    continue
                await bot.send_file(user.forum_id, file=files,
                                    caption=f"🗑\n{messages_list[0].text}",
                                    reply_to=messages_list[0].chat.topic_id)

    @staticmethod
    async def handle_messages(client: "Client", messages: list[Message], caption: str | None = None):
        user_id = await client.get_id()
        user = await client.db.get_user_by_id(user_id)

        async with client.lock:
            if (chat := await client.db.get_chat_by_id(user, messages[0].chat_id)) is None:
                _chat_obj = await messages[0].get_chat()
                if _chat_obj is None:
                    for dialog in await client.get_dialogs(10, offset_date=messages[0].date+timedelta(minutes=1)):
                        if dialog.id == messages[0].chat_id:
                            _chat_obj = dialog.entity
                            break
                    else:
                        logging.info(f"Chat with ID {messages[0].chat_id} not found for user {user_id}")
                        return
                chat = await client.client_service.create_chat(client, _chat_obj, user, client.bot)

        if chat.blacklisted:
            return

        messages_obj: list[DBMessage] = []
        for message in messages:
            if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)) and message.media.ttl_seconds:
                await MessageService.handle_onetime_message(client, message)
                return

            async with client.lock:
                if not (msg := await client.db.get_message(user, message.id)):
                    msg = await client.db.add_message(user, chat, message.id, message.message,
                                                      int(message.date.timestamp()), message.grouped_id
                                                      )
            messages_obj.append(msg)

        bot = client.bot
        bot_obj = await client.db.get_bot(await bot.get_id())

        if messages[0].sticker:
            attachment = await client.db.get_attachment(bot_obj, messages[0].sticker.id, chat)
            if not attachment:
                send_message = await bot.send_file(user.forum_id, messages[0].sticker, message=messages[0].message,
                                                   reply_to=user.files_topic_id)
                attachment = await client.db.add_attachment(bot_obj, send_message.id, send_message.document.id)
            messages_obj[0].attachment = attachment
            await messages_obj[0].save()

        elif isinstance(messages[0].media, (MessageMediaPhoto, MessageMediaDocument)):
            files = [await client.file_service.download_message_media(client, message) for message in messages]
            files = files[0] if len(files) == 1 else files
            caption = f"[Topic](https://t.me/c/{user.forum_id}/{chat.topic_id})"
            send_messages = await bot.send_file(user.forum_id, files, reply_to=user.files_topic_id, caption=caption)
            if isinstance(send_messages, Message):
                send_messages = [send_messages]

            for send_message, message_obj in zip(send_messages, messages_obj):
                attachment = await client.db.add_attachment(bot_obj, send_message.id, send_message.file.media.id)
                message_obj.attachment = attachment
                await message_obj.save()

    @staticmethod
    async def handle_difference(client: "Client"):
        state = client.session.get_update_state(0)
        if not state:
            return
        
        logging.info("Processing message differences (synchronizing missed messages)...")
        diff = await client.get_difference(state)

        if isinstance(diff, DifferenceEmpty):
            logging.info("No message differences found - client is up to date")
            return

        new_messages = list(filter(lambda m: not m.out, diff.new_messages))
        deleted_messages_count = sum(1 for update in diff.other_updates if isinstance(update, UpdateDeleteMessages))
        
        if new_messages or deleted_messages_count > 0:
            logging.info(f"Processing {len(new_messages)} new messages and {deleted_messages_count} deletion events")
        
        events = MessageService.parse_messages_to_events(new_messages)
        for event in events:
            await MessageService.handle_message_event(client, event)

        for update in diff.other_updates:
            if isinstance(update, UpdateDeleteMessages):
                await MessageService.handle_deleted_message(client, update.messages)

        if isinstance(diff, Difference):
            new_state = diff.state
            client.session.set_update_state(0, new_state)
            logging.info("Message synchronization completed successfully")
        elif isinstance(diff, DifferenceSlice):
            new_state = diff.intermediate_state
            client.session.set_update_state(0, new_state)
            logging.info("Processing additional message differences (continuing synchronization)...")
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
