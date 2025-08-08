from telethon import TelegramClient

from telethon.tl import types, functions

from typing import TYPE_CHECKING

from core.messageService import MessageService

if TYPE_CHECKING:
    from TeleWatch import TeleWatch


class Client(TelegramClient):
    def __init__(self, session, telewatch: "TeleWatch", *args, **kwargs):
        session = f"sessions/{session}"
        super().__init__(session, *args, **kwargs)
        self.telewatch = telewatch
        self.__client_tg_id = None

    @property
    def db(self):
        return self.telewatch.db

    @property
    def bot(self):
        return self.telewatch.bot

    async def get_id(self):
        if self.__client_tg_id is None:
            self.__client_tg_id = (await self.get_me()).id
        return self.__client_tg_id

    async def configure(self):
        await self.init_dialogs()
        pass

    async def create_topic(self, channel_id, title: str):
        update: types.Updates = await self(functions.channels.CreateForumTopicRequest(channel_id, title))
        return update.updates[0].id

    async def init_dialogs(self):
        await self.iter_dialogs(1).collect()
