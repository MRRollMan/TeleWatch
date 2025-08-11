from tortoise import run_async, Tortoise
from database.models import User, Chat, Message


class Database:
    @staticmethod
    async def init_database():
        await Tortoise.init(
            db_url='sqlite://db.sqlite3',
            modules={'models': ['database.models']}
        )
        # Generate the schema
        await Tortoise.generate_schemas()

    @staticmethod
    async def add_user(user_id: int, forum_id: int = 0):
        return await User.get_or_create(user_id=user_id, forum_id=forum_id)

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
    async def add_chat(user: User, chat_id: int, topic_id: int):
        return await Chat.get_or_create(user=user, chat_id=chat_id, topic_id=topic_id)

    @staticmethod
    async def has_chat(user: User, chat_id: int):
        return await Chat.get_or_none(chat_id=chat_id, user=user) is not None

    @staticmethod
    async def get_chat_by_id(user: User, chat_id: int):
        return await Chat.get_or_none(chat_id=chat_id, user=user)

    @staticmethod
    async def add_message(user: User, chat: Chat, message_id: int, text: str, date: int):
        if user is None or chat is None:
            return None
        return await Message.get_or_create(user=user, chat=chat, message_id=message_id, text=text, date=date)

    @staticmethod
    async def get_messages(user: User):
        return await user.messages.all()

    @staticmethod
    async def get_message_by_chat(user: User, chat: Chat, message_id) -> Message | None:
        return await Message.get_or_none(message_id=message_id, chat=chat, user=user).prefetch_related("chat", "user")

    @staticmethod
    async def get_message(user: User, message_id) -> Message | None:
        return await Message.get_or_none(message_id=message_id, user=user).prefetch_related("chat", "user")
