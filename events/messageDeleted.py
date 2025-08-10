from telethon import events
from telethon.tl.types import UpdateDeleteMessages

from core.messageService import MessageService


@events.register(events.MessageDeleted)
async def message_deleted_handler(event: events.messagedeleted.MessageDeleted.Event):
    if isinstance(event.original_update, UpdateDeleteMessages):
        await MessageService.handle_deleted_message(event.client, event.deleted_ids)
