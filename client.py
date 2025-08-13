import asyncio
import datetime
from typing import TYPE_CHECKING

from telethon import TelegramClient
from telethon.tl import types, functions
from telethon.tl.types import InputNotifyForumTopic, InputPeerNotifySettings
from telethon.tl.types.updates import State, Difference, DifferenceSlice

from config import Config
from core.messageService import MessageService

if TYPE_CHECKING:
    from TeleWatch import TeleWatch
    from telethon.sessions import Session


class Client(TelegramClient):
    session: "Session"
    
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
        uid = await self.get_id()
        if await self.is_bot() and await self.db.has_bot(uid):
            await self.db.add_bot(uid)
        elif await self.db.has_user(uid):
            await MessageService.handle_difference(self)
        else:
            await self.init_user_data(uid)
            await self.get_dialogs()

    async def init_user_data(self, user_id: int):
        """
        Initializes user data by creating a forum and adding user to a database.
        """
        forum_id = await self.create_forum(Config.get_forum_title(), Config.get_forum_about())
        topic_id = await self.create_topic(forum_id, Config.get_files_topic_title())
        await self.mute_topic(forum_id, topic_id)
        await self.update_pined_topic(forum_id, topic_id)
        await self.db.add_user(user_id, forum_id, topic_id)

    async def create_forum(self, title: str, about: str):
        update: types.Updates = await self(functions.channels.CreateChannelRequest(title, about, forum=True))
        return update.chats[0].id

    async def create_topic(self, channel_id, title: str):
        update: types.Updates = await self(functions.channels.CreateForumTopicRequest(channel_id, title))
        return update.updates[0].id

    async def mute_topic(self, channel_id, topic_id):
        input_channel = await self.get_input_entity(channel_id)
        await self(functions.account.UpdateNotifySettingsRequest(
            peer=InputNotifyForumTopic(input_channel, topic_id),
            settings=InputPeerNotifySettings(
                mute_until=datetime.datetime(year=2038, month=1, day=1, hour=1, minute=1, second=1),
                show_previews=True
            )
        ))

    async def update_pined_topic(self, channel_id, topic_id, pinned: bool = True):
        return await self(functions.channels.UpdatePinnedForumTopicRequest(
            channel=channel_id,
            topic_id=topic_id,
            pinned=pinned
        ))

    async def add_chat_user(self, chat_id, user):
        return await self(functions.channels.InviteToChannelRequest(chat_id, [user]))

    async def get_difference(self, state: State) -> Difference | DifferenceSlice:
        return await self(functions.updates.GetDifferenceRequest(
            pts=state.pts,
            date=state.date,
            qts=state.qts,
        ))

    async def edit_admin(self, channel, user_id, change_info: bool = None,
                         post_messages: bool = None,
                         edit_messages: bool = None,
                         delete_messages: bool = None,
                         ban_users: bool = None,
                         invite_users: bool = None,
                         pin_messages: bool = None,
                         add_admins: bool = None,
                         manage_call: bool = None,
                         anonymous: bool = None,
                         is_admin: bool = None,
                         other: bool = None,
                         manage_topics: bool = None,
                         post_stories: bool = None,
                         edit_stories: bool = None,
                         delete_stories: bool = None,
                         title: str = ""):
        return await self(functions.channels.EditAdminRequest(
            channel=channel,
            user_id=user_id,
            admin_rights=types.ChatAdminRights(
                change_info=change_info,
                post_messages=post_messages,
                edit_messages=edit_messages,
                delete_messages=delete_messages,
                ban_users=ban_users,
                invite_users=invite_users,
                pin_messages=pin_messages,
                add_admins=add_admins,
                anonymous=anonymous,
                manage_call=manage_call,
                other=other,
                manage_topics=manage_topics,
                post_stories=post_stories,
                edit_stories=edit_stories,
                delete_stories=delete_stories,
            ),
            rank=title
        ))
