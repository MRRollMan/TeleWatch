from tortoise import Tortoise

from config import Config
from database.models import User, Chat, Message, Attachment, Bot


class Database:
    @staticmethod
    async def init_database():
        await Tortoise.init(
            db_url=Config.get_db_url(),
            modules={'models': ['database.models']}
        )

        # Generate the schema
        await Tortoise.generate_schemas()

    @staticmethod
    async def close():
        await Tortoise.close_connections()

    @staticmethod
    async def add_user(user_id: int, forum_id: int = 0, files_topic_id: int = 0) -> User:
        return (await User.get_or_create(user_id=user_id, forum_id=forum_id, files_topic_id=files_topic_id))[0]

    @staticmethod
    async def has_user(user_id: int):
        return await User.get_or_none(user_id=user_id) is not None

    @staticmethod
    async def get_user_by_id(user_id: int) -> User:
        return await User.get_or_none(user_id=user_id)

    @staticmethod
    async def set_user_forum_id(user: User, forum_id: int):
        user.forum_id = forum_id
        return await user.save()

    @staticmethod
    async def set_user_files_topic_id(user: User, files_topic_id: int):
        user.files_topic_id = files_topic_id
        return await user.save()

    @staticmethod
    async def add_chat(user: User, chat_id: int, topic_id: int, is_bot: bool) -> Chat:
        return (await Chat.get_or_create(user=user,
                                         chat_id=chat_id,
                                         topic_id=topic_id,
                                         is_bot=is_bot,
                                         blacklisted=is_bot
                                         ))[0]

    @staticmethod
    async def has_chat(user: User, chat_id: int):
        return await Chat.get_or_none(chat_id=chat_id, user=user) is not None

    @staticmethod
    async def get_chat_by_id(user: User, chat_id: int) -> Chat | None:
        return await Chat.get_or_none(chat_id=chat_id, user=user)

    @staticmethod
    async def add_message(user: User, chat: Chat, message_id: int, text: str, date: int, grouped_id: int = None) -> Message:
        return (await Message.get_or_create(
            user=user,
            chat=chat,
            message_id=message_id,
            text=text,
            date=date,
            grouped_id=grouped_id
        ))[0]

    @staticmethod
    async def get_messages(user: User):
        return await user.messages.all()

    @staticmethod
    async def get_message_by_chat(user: User, chat: Chat, message_id) -> Message | None:
        return await Message.get_or_none(message_id=message_id, chat=chat, user=user).prefetch_related("chat", "user")

    @staticmethod
    async def get_message(user: User, message_id) -> Message | None:
        return await (Message.get_or_none(message_id=message_id, user=user).
                      prefetch_related("chat", "user", "attachment", "attachment__bot"))

    @staticmethod
    async def get_grouped_message(user: User, grouped_id) -> Message | None:
        return await Message.get_or_none(grouped_id=grouped_id, user=user).prefetch_related("chat", "user")

    @staticmethod
    async def add_bot(bot_id: int):
        return await Bot.get_or_create(bot_id=bot_id)

    @staticmethod
    async def has_bot(bot_id: int) -> bool:
        return await Bot.get_or_none(bot_id=bot_id) is not None

    @staticmethod
    async def get_bot(bot_id: int) -> Bot | None:
        return await Bot.get_or_none(bot_id=bot_id)

    @staticmethod
    async def add_attachment(bot_id: int, topic_message_id: int, file_id: str):
        return (await Attachment.get_or_create(
            bot=bot_id,
            topic_message_id=topic_message_id,
            file_id=file_id
        ))[0]

    @staticmethod
    async def get_attachment(bot_id: int, file_id: str) -> Attachment | None:
        return await Attachment.get_or_none(
            bot=bot_id,
            file_id=file_id
        ).prefetch_related("bot", "messages", "messages__chat", "messages__user")
