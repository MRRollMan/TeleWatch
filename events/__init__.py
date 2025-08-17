from typing import Callable

from events.newMessage import new_message_handler, album_message_handler
from events.userUpdate import user_update_handler
from events.messageDeleted import message_deleted_handler
from telethon.events import is_handler


def get_events() -> list[Callable]:
    a = globals().copy()
    my_events = []
    for e in a.values():
        if is_handler(e):
            my_events.append(e)
    return my_events


__all__ = ['get_events']
