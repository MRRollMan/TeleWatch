from tortoise.models import Model
from tortoise import fields


class User(Model):
    user_id = fields.IntField(pk=True)
    forum_id = fields.IntField()
    files_topic_id = fields.IntField()
    ignore_users = fields.BooleanField(default=False)
    ignore_groups = fields.BooleanField(default=True)
    ignore_channels = fields.BooleanField(default=True)

    chats = fields.ReverseRelation["Chat"]
    messages = fields.ReverseRelation["Message"]


class Bot(Model):
    bot_id = fields.IntField(pk=True)
    attachments = fields.ReverseRelation["Attachment"]


class Chat(Model):
    id = fields.IntField(pk=True)
    chat_id = fields.IntField()
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="chats")
    topic_id = fields.IntField()
    whitelisted = fields.BooleanField(default=False)
    blacklisted = fields.BooleanField(default=False)
    is_bot = fields.BooleanField(default=False)

    messages = fields.ReverseRelation["Message"]


class Message(Model):
    id = fields.IntField(pk=True)
    message_id = fields.IntField(required=True)
    grouped_id = fields.IntField(null=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="messages")
    chat: fields.ForeignKeyRelation[Chat] = fields.ForeignKeyField("models.Chat", related_name="messages")
    attachment: fields.ForeignKeyRelation["Attachment"] = fields.ForeignKeyField(
        "models.Attachment", related_name="messages", null=True)
    text = fields.TextField(null=True)
    date = fields.DatetimeField()
    deleted = fields.BooleanField(default=False)


class Attachment(Model):
    id = fields.IntField(pk=True)
    bot: fields.ForeignKeyRelation[Bot] = fields.ForeignKeyField("models.Bot", related_name="attachments")
    topic_message_id = fields.IntField()
    file_id = fields.CharField(max_length=255, required=True)

    messages: fields.ReverseRelation["Message"]
