import json


class Config:
    with open("config.json", "r") as file:
        config = json.load(file)

    @classmethod
    def get_app_id(cls):
        return cls.config["app_id"]

    @classmethod
    def get_app_hash(cls):
        return cls.config["app_hash"]

    @classmethod
    def get_users(cls):
        return cls.config["users"]

    @classmethod
    def get_bots(cls):
        return cls.config["bots"]

    @classmethod
    def get_forum_title(cls):
        return cls.config["forum_title"]

    @classmethod
    def get_forum_about(cls):
        return cls.config["forum_about"]

    @classmethod
    def get_files_topic_title(cls):
        return cls.config["files_topic_title"]

    @classmethod
    def get_db_url(cls):
        return cls.config["db_url"]
