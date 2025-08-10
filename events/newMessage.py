from telethon import events

from core.messageService import MessageService


@events.register(events.NewMessage(outgoing=False))
async def new_message_handler(event: events.newmessage.NewMessage.Event):
    await MessageService.handle_message(event.client, event.message)
