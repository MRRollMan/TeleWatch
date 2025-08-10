import asyncio
import logging
from itertools import cycle

from telethon.errors import AccessTokenInvalidError

from client import Client
from config import Config
from core.messageService import MessageService
from core.botService import BotService
from database import Database
from events import get_events
from telethon.tl import functions


def get_password_input():
    return input('Enter your password: ')


# TODO: Move this to core module
async def create_forum(client, db):
    client_id = await client.get_id()
    forum_id = (await db.get_user_by_id(client_id)).forum_id
    if forum_id is not None and forum_id != 0:
        return
    update = await client(functions.channels.CreateChannelRequest("TeleWatch", "TeleWatch", forum=True))
    forum_id = update.chats[0].id
    return forum_id


# TODO: Move this to core module
async def init_user_data(client, db):
    client_id = await client.get_id()
    if not await db.has_user(client_id):
        user = (await db.add_user(client_id))[0]
        forum_id = await create_forum(client, db)
        if forum_id is not None:
            await db.set_user_forum_id(user, forum_id)


class TeleWatch:
    def __init__(self):
        self.api_id = Config.get_app_id()
        self.api_hash = Config.get_app_hash()
        self.db = Database()
        self.message_service = MessageService()
        self.events = get_events()
        self.clients: list[Client] = []
        self.bots: list[Client] = []
        self.__bots: cycle[Client] | None = None

    async def init_users(self):
        for user in Config.get_users():
            client = await self.init_client(user)
            if not await self.db.has_user(await client.get_id()):
                await init_user_data(client, self.db)
            await client.configure()

            self.clients.append(client)
            for bot in self.bots:
                if not await BotService.in_user_forum(client, bot):
                    await BotService.add_bot_to_forum(client, bot)

    async def init_client(self, user: dict) -> Client:
        session_name: str = user.get("name")
        phone: str = user.get("phone")
        password: str = user.get("password")
        if not session_name or not phone:
            raise ValueError("User configuration must contain 'name' and 'phone'.")
        client = Client(session_name, self, api_id=self.api_id, api_hash=self.api_hash, device_model="хтивка",
                        app_version="1.0")
        await client.start(phone, password if password else get_password_input)
        self.init_events(client)
        await client.init_dialogs()

        return client

    async def init_bots(self):
        for bot in Config.get_bots():
            token = bot.get("token")
            name = bot.get("name")
            if not name:
                raise ValueError("Bot configuration must contain 'name'.")
            if not token:
                raise ValueError("Bot configuration must contain 'token'.")
            bot = Client(name, self, api_id=self.api_id, api_hash=self.api_hash)
            try:
                await bot.start(bot_token=token)
            except AccessTokenInvalidError as e:
                bot.disconnect()
                logging.error(f"Invalid token for bot {name}: {e}")
                continue

            self.bots.append(bot)
        if not self.bots:
            raise ValueError("No valid bots configured. Please check your configuration file.")
        self.__bots = cycle(self.bots)

    @property
    def bot(self):
        if not self.__bots:
            raise ValueError("Bots are not initialized. Configure them in the config file.")
        return next(self.__bots)

    def init_events(self, client: Client):
        for event in self.events:
            client.add_event_handler(event)

    def _stop(self):
        for client in self.clients:
            client.disconnect()
        if self.__bots:
            for bot in list(self.bots):
                bot.disconnect()
        logging.info("TeleWatch stopped successfully.")

    async def _start(self):
        await self.init_bots()
        await self.init_users()
        for client in self.clients:
            await client.disconnected

    def start(self):
        self.db.init_database()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._start())
        except KeyboardInterrupt:
            logging.info("Stopping TeleWatch...")
            self._stop()

