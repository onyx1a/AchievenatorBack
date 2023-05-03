import json
from json import JSONEncoder
from typing import Any


class GameInfo:
    def __init__(self) -> None:
        self.app_id = 0
        self.title = ""
        self.achievements_count = 0
        self.achievements_done = 0
        self.achievements_info = []

    @property
    def score(self) -> int:
        return self.achievements_count - self.achievements_done

    @property
    def url_link(self) -> str:
        return f"https://store.steampowered.com/app/{self.app_id}"

    @property
    def icon_url(self) -> str:
        return f"https://media.steampowered.com/steamcommunity/public/images/apps/{self.app_id}/{self.img_icon_url_hash}.jpg"

    def serialize(self):
        return {
            "app_id": self.app_id,
            "title": self.title,
            "a_count": self.achievements_count,
            "a_done": self.achievements_done,
            "a_info": self.achievements_info,
        }

    def to_json(self):
        return json.dumps(self.__dict__)


class GameInfoEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        return o.__dict__
