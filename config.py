import json

class Config:
    __file = open("config.json", "r")
    config = json.load(__file)

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
