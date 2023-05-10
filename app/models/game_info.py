from dataclasses import dataclass


@dataclass
class GameInfo:
    app_id: int = 0
    title: str = ""
    achievements_count: int = 0
    achievements_done: int = 0
    achievements_info = None

    def __post_init__(self):
        if self.achievements_info is None:
            self.achievements_info = []

    def serialize(self):
        return {
            "app_id": self.app_id,
            "title": self.title,
            "a_count": self.achievements_count,
            "a_done": self.achievements_done,
            "a_info": self.achievements_info,
        }
