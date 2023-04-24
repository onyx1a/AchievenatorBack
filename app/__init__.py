import os
import requests
import aiohttp
import asyncio

from requests.exceptions import ConnectTimeout
from flask import Flask, jsonify
from flask_caching import Cache

from app.models.game_info import GameInfo
from profiler import Profiler

config = {"DEBUG": True, "CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)


GAME_LIST_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
GAME_INFO_URL = (
    "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
)
STEAM_SECRET_KEY = os.environ["STEAM_SECRET_KEY"]
DEFAULT_REQUEST_TIMEOUT = 1


def get_game_list(steamid):
    payload = {
        "key": STEAM_SECRET_KEY,
        "steamid": steamid,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json",
    }
    print("Getting data about games...")
    prof = Profiler()
    games_list = []
    try:
        data = requests.get(GAME_LIST_URL, params=payload, timeout=DEFAULT_REQUEST_TIMEOUT)
        if data.status_code == 200:
            games_list = data.json()["response"]["games"]
            print(f"Found {len(games_list)} games in {prof.elapsed}s")
            success = True
        else:
            success = False
        return games_list, success, data.status_code
    except ConnectTimeout:
        return [], False, -1


def get_game_info(game, steamid):
    app_id = game["appid"]
    payload = {"appid": app_id, "key": STEAM_SECRET_KEY, "steamid": steamid}
    data = requests.get(GAME_INFO_URL, params=payload, timeout=DEFAULT_REQUEST_TIMEOUT)
    info = data.json()["playerstats"]
    try:
        # done_achievements = 0
        done_achievements = sum(1 for achievement_data in info["achievements"] if achievement_data["achieved"] == 1)
        all_ach = len(info["achievements"])

        game_info = GameInfo(
            app_id, info["gameName"], all_ach, done_achievements, game["img_icon_url"]
        )
        return game_info
    except KeyError:
        return None
    except ConnectTimeout:
        return None


@app.route("/data/<steamid>")
def index(steamid):
    games_list, status, code = get_game_list(steamid)
    game_data = []
    overall_ach_count = 0
    overall_done_ach_count = 0
    print("Start parsing games...")
    prof = Profiler()
    for game in games_list:
        # print(g)
        # prof2 = Profiler()
        info = get_game_info(game, steamid)
        if info:
            game_data.append(info.serialize())
            overall_ach_count += info.achievements_count
            overall_done_ach_count += info.achievements_done
        # print(prof2.elapsed)
    print("Done at", prof.elapsed)
    prof.reload()
    print("Sorting list")
    # if game_data:
    #     game_data.sort(key=lambda a: a.score)
    print("Done at", prof.elapsed)
    # overall_done_ach_count = 10
    # overall_ach_count = 20
    return jsonify(
        {
            "status": status,
            "code": code,
            "overall_done_ach_count": overall_done_ach_count,
            "overall_ach_count": overall_ach_count,
            "game_data": game_data,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
