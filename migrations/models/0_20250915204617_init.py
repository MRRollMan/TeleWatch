from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "bot" (
    "bot_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
);
CREATE TABLE IF NOT EXISTS "attachment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "topic_message_id" INT NOT NULL,
    "file_id" VARCHAR(255) NOT NULL,
    "bot_id" INT NOT NULL REFERENCES "bot" ("bot_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user" (
    "user_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "forum_id" INT NOT NULL,
    "files_topic_id" INT NOT NULL,
    "ignore_users" INT NOT NULL DEFAULT 0,
    "ignore_groups" INT NOT NULL DEFAULT 1,
    "ignore_channels" INT NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS "chat" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "chat_id" INT NOT NULL,
    "topic_id" INT NOT NULL,
    "whitelisted" INT NOT NULL DEFAULT 0,
    "blacklisted" INT NOT NULL DEFAULT 0,
    "is_bot" INT NOT NULL DEFAULT 0,
    "user_id" INT NOT NULL REFERENCES "user" ("user_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "message" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "message_id" INT NOT NULL,
    "grouped_id" INT,
    "text" TEXT,
    "date" TIMESTAMP NOT NULL,
    "deleted" INT NOT NULL DEFAULT 0,
    "attachment_id" INT REFERENCES "attachment" ("id") ON DELETE CASCADE,
    "chat_id" INT NOT NULL REFERENCES "chat" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "user" ("user_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
