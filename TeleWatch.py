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


class TeleWatch:
    def __init__(self):
        self.api_id = Config.get_app_id()
        self.api_hash = Config.get_app_hash()
        self.db = Database()
        self.message_service = MessageService()
        self.events = get_events()
        self.clients: list[Client] = []
        self.bots: dict[int, Client] = {}
        self.__bots: cycle[Client] | None = None

    async def init_users(self):
        for user in Config.get_users():
            client = await self.init_client(user)
            await client.configure()

            self.clients.append(client)
            for bot in self.bots.values():
                if not await BotService.in_user_forum(client, bot):
                    await BotService.add_bot_to_forum(client, bot)

    async def init_client(self, user: dict) -> Client:
        session_name: str | None = user.get("name")
        phone: str | None = user.get("phone")
        password: str | None = user.get("password")
        if not session_name or not phone:
            raise ValueError("User configuration must contain 'name' and 'phone'.")
        client = Client(session_name, self, api_id=self.api_id, api_hash=self.api_hash, device_model="хтивка",
                        app_version="1.0")
        self.init_events(client)
        await client.start(phone, password)

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

            await bot.configure()
            bot_id = await bot.get_id()
            self.bots[bot_id] = bot
        if not self.bots:
            raise ValueError("No valid bots configured. Please check your configuration file.")
        self.__bots = cycle(self.bots.values())

    @property
    def bot(self):
        if self.__bots is None:
            raise ValueError("Bots have not been initialized. Call start() first.")
        return next(self.__bots)

    def get_bot(self, bot_id: int) -> Client:
        if bot_id not in self.bots:
            raise ValueError(f"Bot with ID {bot_id} does not exist.")
        return self.bots[bot_id]

    def init_events(self, client: Client):
        for event in self.events:
            client.add_event_handler(event)

    def _stop(self):
        for client in self.clients:
            client.disconnect()
        if self.__bots:
            for bot in list(self.bots.values()):
                bot.disconnect()
        logging.info("TeleWatch stopped successfully.")

    async def _start(self):
        await self.db.init_database()
        await self.init_bots()
        await self.init_users()
        for client in self.clients:
            await client.disconnected

    def start(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._start())
        except KeyboardInterrupt:
            logging.info("Stopping TeleWatch...")
            self._stop()
