import time
from io import BytesIO

from telethon.tl.custom import Message
from telethon.tl.types import MessageMediaPhoto, DocumentAttributeFilename, MessageMediaDocument, \
    DocumentAttributeVideo, DocumentAttributeAudio


class FileService:
    @staticmethod
    async def download_message_media(client, message: Message) -> BytesIO:
        if not message.media:
            raise ValueError("Message does not contain media.")

        file = BytesIO(await client.download_media(message, file=bytes))
        file.name = FileService.get_filename(message)

        return file

    @staticmethod
    def get_filename(message: Message) -> str:
        if not message.media:
            raise ValueError("Message does not contain media.")
        ext = str()
        additional_info = []
        if isinstance(message.media, MessageMediaPhoto):
            ext = 'jpg'
        elif isinstance(message.media, MessageMediaDocument) and message.media.document:
            for attr in message.media.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    return attr.file_name
                elif isinstance(attr, DocumentAttributeVideo):
                    ext = 'mp4'
                    if attr.round_message:
                        additional_info.append("round_video")
                elif isinstance(attr, DocumentAttributeAudio) and attr.voice:
                    additional_info.append("voice")
                    ext = 'ogg'
        if ext:
            return f"{message.id}_{time.time()}{"_"+("".join(additional_info))}.{ext}"
        raise ValueError("Unsupported media type in message.")
