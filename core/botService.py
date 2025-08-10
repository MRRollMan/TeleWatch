from telethon.tl.types import Channel, ChannelParticipantsBots

from client import Client


class BotService:
    @staticmethod
    async def in_user_forum(client: "Client", bot: "Client") -> bool:
        user_id = await client.get_id()
        bot_id = await bot.get_id()

        user = await client.db.get_user_by_id(user_id)
        forum = await client.get_entity(user.forum_id)
        if not isinstance(forum, Channel):
            raise TypeError("Invalid forum type")
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
        if not isinstance(forum, Channel):
            raise TypeError("Invalid forum type")
        if not forum.forum:
            raise TypeError("Invalid forum type")

        await client.add_chat_user(forum.id, await bot.get_id())

