import asyncio
from typing import TYPE_CHECKING

from telethon import TelegramClient
from telethon.tl import types, functions
from telethon.tl.types.updates import State, Difference, DifferenceSlice

from config import Config
from core.messageService import MessageService

if TYPE_CHECKING:
    from TeleWatch import TeleWatch


class Client(TelegramClient):
    def __init__(self, session, telewatch: "TeleWatch", *args, **kwargs):
        session = f"sessions/{session}"
        super().__init__(session, *args, **kwargs)
        self.telewatch = telewatch
        self.__me = None
        self.lock = asyncio.Lock()

    @property
    def db(self):
        return self.telewatch.db

    @property
    def bot(self):
        return self.telewatch.bot

    @property
    async def me(self):
        if self.__me is None:
            self.__me = await self.get_me()
        return self.__me

    async def get_id(self):
        return (await self.me).id

    async def configure(self):
        if await self.db.has_user(await self.get_id()):
            await MessageService.handle_difference(self)
        else:
            await self.init_user_data()
            await self.get_dialogs()

    async def init_user_data(self):
        """
        Initializes user data by creating a forum and adding user to a database.
        """
        client_id = await self.get_id()
        forum_id = await self.create_forum(Config.get_forum_title(), Config.get_forum_about())
        await self.db.add_user(client_id, forum_id)

    async def create_forum(self, title: str, about: str):
        update: types.Updates = await self(functions.channels.CreateChannelRequest(title, about, forum=True))
        return update.chats[0].id

    async def create_topic(self, channel_id, title: str):
        update: types.Updates = await self(functions.channels.CreateForumTopicRequest(channel_id, title))
        return update.updates[0].id

    async def add_chat_user(self, chat_id, user):
        return await self(functions.channels.InviteToChannelRequest(chat_id, [user]))

    async def get_difference(self, state: State) -> Difference | DifferenceSlice:
        return await self(functions.updates.GetDifferenceRequest(
            pts=state.pts,
            date=state.date,
            qts=state.qts,
        ))
