import json
from json import JSONEncoder
from typing import Any


class GameInfo:
    def __init__(
        self,
        app_id: int,
        title: str,
        achievements_count: int,
        achievements_done: int,
        img_icon_url: str,
    ) -> None:
        self.app_id = app_id
        self.title = title
        self.achievements_count = achievements_count
        self.achievements_done = achievements_done
        self.img_icon_url_hash = img_icon_url

    @property
    def score(self) -> int:
        return self.achievements_count - self.achievements_done

    @property
    def url_link(self) -> str:
        return f"https://store.steampowered.com/app/{self.app_id}"

    @property
    def icon_url(self) -> str:
        return f"https://media.steampowered.com/steamcommunity/public/images/apps/{self.app_id}/{self.img_icon_url_hash}.jpg"

    # def __repr__(self):
    #     return f"app_id\": {self.app_id}, \"gameTitle\": \"{self.title}\", \"achievements_count\": {self.achievements_count}, \"achievements_done\": {self.achievements_done}, \"img_icon_url_hash\": \"{self.img_icon_url_hash}"
    #
    # def __str__(self):
    #     return f"app_id\": {self.app_id}, \"gameTitle\": \"{self.title}\", \"achievements_count\": {self.achievements_count}, \"achievements_done\": {self.achievements_done}, \"img_icon_url_hash\": \"{self.img_icon_url_hash}"
    #

    def serialize(self):
        return {
            "app_id": self.app_id,
            "title": self.title,
            # "score": self.score,
            "img_icon_url_hash": self.img_icon_url_hash,
            "achievements_count": self.achievements_count,
            "achievements_done": self.achievements_done
        }

    def to_json(self):
        return json.dumps(self.__dict__)


class GameInfoEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        return o.__dict__
