import asyncio

from telethon import TelegramClient

from telethon.tl import types, functions

from typing import TYPE_CHECKING

from telethon.tl.types.updates import State, Difference, DifferenceSlice

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

    async def configure(self, has_user: bool):
        if not has_user:
            await self.init_dialogs()
        else:
            await MessageService.handle_difference(self)

    async def create_topic(self, channel_id, title: str):
        update: types.Updates = await self(functions.channels.CreateForumTopicRequest(channel_id, title))
        return update.updates[0].id

    async def add_chat_user(self, chat_id, user):
        return await self(functions.channels.InviteToChannelRequest(chat_id, [user]))

    async def init_dialogs(self):
        await self.get_dialogs()

    async def get_difference(self, state: State) -> Difference | DifferenceSlice:
        return await self(functions.updates.GetDifferenceRequest(
            pts=state.pts,
            date=state.date,
            qts=state.qts,
        ))
