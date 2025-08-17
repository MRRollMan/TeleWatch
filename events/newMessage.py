from telethon import events

from core.messageService import MessageService


@events.register(events.Album)
async def album_message_handler(event: events.album.Album.Event):
    await MessageService.handle_message_event(event.client, event)


@events.register(events.NewMessage(outgoing=False))
async def new_message_handler(event: events.newmessage.NewMessage.Event):
    if event.message.grouped_id:
        return
    await MessageService.handle_message_event(event.client, event)
