from telethon import events
from telethon.types import Message


@events.register(events.UserUpdate)
async def user_update_handler(event: events.userupdate.UserUpdate.Event):
    pass
