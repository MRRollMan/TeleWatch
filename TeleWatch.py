import asyncio
import logging
from itertools import cycle

from telethon.errors import AccessTokenInvalidError

from client import Client
from config import Config
from database import Database
from events import get_events


class TeleWatch:
    def __init__(self):
        self.api_id = Config.get_app_id()
        self.api_hash = Config.get_app_hash()
        self.db = Database()
        self.events = get_events()
        self.clients: list[Client] = []
        self.bots: dict[int, Client] = {}
        self.__bots: cycle[Client] | None = None

    async def init_users(self):
        logging.info(f"Initializing {len(Config.get_users())} user client(s)...")
        for user in Config.get_users():
            client = await self.init_client(user)
            await client.client_service.configure_client(client)

            self.clients.append(client)
            logging.info(f"User client '{user.get('name')}' initialized successfully")
            
            for bot in self.bots.values():
                if not await client.client_service.bot_in_user_forum(client, bot):
                    await client.client_service.add_bot_to_forum(client, bot)

    async def init_client(self, user: dict) -> Client:
        session_name: str | None = user.get("name")
        phone: str | None = user.get("phone")
        password: str | None = user.get("password")
        api_id = user.get("api_id", self.api_id)
        api_hash = user.get("api_hash", self.api_hash)
        if not session_name or not phone:
            raise ValueError("User configuration must contain 'name' and 'phone'.")
        client = Client(session_name,
                        self,
                        api_id=api_id or self.api_id,
                        api_hash=api_hash or self.api_hash,
                        device_model=Config.get_forum_title(),
                        app_version="1.0")
        self.init_events(client)
        await client.start(phone, password)

        return client

    async def init_bots(self):
        logging.info(f"Initializing {len(Config.get_bots())} bot client(s)...")
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
                logging.info(f"Bot '{name}' connected successfully")
            except AccessTokenInvalidError as e:
                bot.disconnect()
                logging.error(f"Invalid token for bot {name}: {e}")
                continue

            await bot.client_service.configure_client(bot)
            bot_id = await bot.get_id()
            self.bots[bot_id] = bot
        if not self.bots:
            raise ValueError("No valid bots configured. Please check your configuration file.")
        self.__bots = cycle(self.bots.values())
        logging.info(f"Successfully initialized {len(self.bots)} bot(s)")

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

    async def _stop(self):
        logging.info("Shutting down TeleWatch...")
        for client in self.clients:
            client.disconnect()
            client.session.close()
        if self.__bots:
            for bot in list(self.bots.values()):
                bot.disconnect()
                bot.session.close()

        await self.db.close()
        logging.info("TeleWatch stopped successfully.")

    async def _start(self):
        logging.info("Starting TeleWatch application...")
        await self.db.init_database()
        await self.init_bots()
        await self.init_users()
        logging.info("TeleWatch started successfully and ready to monitor messages")
        for client in self.clients:
            await client.disconnected

    def start(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._start())
        except KeyboardInterrupt:
            logging.info("Stopping TeleWatch...")
            loop.run_until_complete(self._stop())
