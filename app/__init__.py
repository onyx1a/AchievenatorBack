import os
import asyncio
import aiohttp

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


async def get_game_list(steamid):
    payload = {
        "key": STEAM_SECRET_KEY,
        "steamid": steamid,
        "include_appinfo": "true",
        "include_played_free_games": "true",
        "format": "json",
    }
    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    print("Getting data about games...")
    prof = Profiler()
    games_list = []
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GAME_LIST_URL, params=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    games_list = data["response"]["games"]
                    print(f"Found {len(games_list)} games in {prof.elapsed}s")
                    success = True
                else:
                    success = False
                return games_list, success, response.status
    except asyncio.TimeoutError:
        return [], False, -1


async def get_game_info_async(game, steamid):
    app_id = game["appid"]
    payload = {"appid": app_id, "key": STEAM_SECRET_KEY, "steamid": steamid}
    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                GAME_INFO_URL, params=payload, timeout=timeout
            ) as response:
                data = await response.json()
                info = data["playerstats"]
                try:
                    done_achievements = sum(
                        1
                        for achievement_data in info["achievements"]
                        if achievement_data["achieved"] == 1
                    )
                    all_ach = len(info["achievements"])

                    game_info = GameInfo(
                        app_id,
                        info["gameName"],
                        all_ach,
                        done_achievements,
                        game["img_icon_url"],
                    )
                    return game_info
                except KeyError:
                    return None
        except asyncio.TimeoutError:
            return None


@app.route("/data/<steamid>")
async def index(steamid):
    games_list, status, code = await get_game_list(steamid)
    game_data = []
    overall_ach_count = 0
    overall_done_ach_count = 0
    print("Start parsing games...")
    prof = Profiler()
    for game in games_list:
        info = await get_game_info_async(game, steamid)
        if info:
            game_data.append(info.serialize())
            overall_ach_count += info.achievements_count
            overall_done_ach_count += info.achievements_done
    print("Done in", prof.elapsed)
    prof.reload()
    print("Sorting list")
    print("Done in", prof.elapsed)
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        pass
    # app.run(debug=True)
