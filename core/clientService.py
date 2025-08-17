from typing import TYPE_CHECKING

from telethon.tl.types import ChannelParticipantsBots

from config import Config
from database.models import User, Chat

if TYPE_CHECKING:
    from client import Client


class ClientService:
    @staticmethod
    async def bot_in_user_forum(client: "Client", bot: "Client") -> bool:
        user_id = await client.get_id()
        bot_id = await bot.get_id()

        user = await client.db.get_user_by_id(user_id)
        forum = await client.get_entity(user.forum_id)
        if not forum.forum:
            raise TypeError("Invalid forum type")

        bots = await client.get_participants(forum, filter=ChannelParticipantsBots)
        for _bot in bots:
            if _bot.id == bot_id:
                return True
        return False

    @staticmethod
    async def add_bot_to_forum(client: "Client", bot: "Client"):
        user = await client.db.get_user_by_id(await client.get_id())
        forum = await client.get_entity(user.forum_id)
        if not forum.forum:
            raise TypeError("Invalid forum type")

        bot_id = await bot.get_id()
        bot_username = (await bot.get_me()).username
        await client.get_entity(bot_username)
        await client.add_chat_user(forum.id, bot_id)
        await client.edit_admin(forum.id, bot_id, is_admin=True, manage_topics=True, pin_messages=True, title="TW")

    @staticmethod
    async def create_chat(client: "Client", chat_id: int, user: User, bot: "Client") -> Chat:
        chat_entity = await client.get_entity(chat_id)
        fullname = f"{chat_entity.first_name} {chat_entity.last_name}" \
            if chat_entity.last_name is not None else chat_entity.first_name
        topic_id = await bot.create_topic(user.forum_id, fullname)
        chat = await client.db.add_chat(user, chat_id, topic_id, chat_entity.bot)
        text = (f"💬: `{fullname}` **({"Bot" if chat_entity.bot else "User"})**\n\n🆔: `{chat_id}`\n"
                f"{f"📱: `{chat_entity.phone}`" if chat_entity.phone else ''}\n"
                f"TopicID: `{topic_id}`\n")
        message = await bot.send_message(user.forum_id, message=text, reply_to=topic_id)
        # Different clients handle the first message of a topic differently, so pin it forcibly.
        await bot.unpin_message(user.forum_id, message)
        await bot.pin_message(user.forum_id, message)

        return chat

    @staticmethod
    async def configure_client(client: "Client"):
        uid = await client.get_id()
        is_bot = await client.is_bot()

        if is_bot and not await client.db.has_bot(uid):
            await client.db.add_bot(uid)
        elif await client.db.has_user(uid):
            await client.message_service.handle_difference(client)
        elif not is_bot:
            await ClientService.init_user_data(client, uid)
            await client.get_dialogs()

    @staticmethod
    async def init_user_data(client: "Client", user_id: int):
        """
        Initializes user data by creating a forum and adding user to a database.
        """
        forum_id = await client.create_forum(Config.get_forum_title(), Config.get_forum_about())
        topic_id = await client.create_topic(forum_id, Config.get_files_topic_title())
        await client.mute_topic(forum_id, topic_id)
        await client.update_pined_topic(forum_id, topic_id)
        await client.db.add_user(user_id, forum_id, topic_id)