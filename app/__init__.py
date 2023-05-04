from urllib.parse import urlparse

import os
import traceback
import asyncio
import aiohttp

from flask import Flask, jsonify
from flask_caching import Cache

from app.utils.custom_response import DefaultResponse, ResponseCode
from app.utils.profiler import InlineProfiler, GlobalProfiler
from app.models.game_info import GameInfo

config = {"DEBUG": True, "CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}

app = Flask(__name__)
app.config.from_mapping(config)
app.json.ensure_ascii = False
app.json.compact = True
cache = Cache(app)
global_profiler = GlobalProfiler()

GAME_LIST_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
GAME_INFO_URL = (
    "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
)
ACHIEVEMENT_INFO_URL = (
    "http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v0002/"
)
STEAM_SECRET_KEY = os.environ["STEAM_SECRET_KEY"]
DEFAULT_REQUEST_TIMEOUT = 1
GAME_COUNT = 5000


@global_profiler.async_profiler
async def fetch_achievements_info(appid, lang):
    async with aiohttp.ClientSession() as session:
        payload = {"key": STEAM_SECRET_KEY, "appid": appid, "l": lang}
        task = asyncio.create_task(fetch_data(session, ACHIEVEMENT_INFO_URL, payload))
        wait_coro = asyncio.wait_for(task, timeout=300)
        result = await wait_coro
        return result[0]


async def fetch_data(session: aiohttp.ClientSession, url, payload):
    async with session.get(url, params=payload) as response:
        return await response.json(), payload


@global_profiler.async_profiler
async def get_game_list(steamid):
    payload = {
        "key": STEAM_SECRET_KEY,
        "steamid": steamid,
        "include_played_free_games": "true",
        "format": "json",
    }
    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    print("Getting data about games...")
    games_list = []
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GAME_LIST_URL, params=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    games_list = data["response"]["games"][:GAME_COUNT]
                    print(f"Found {len(games_list)} games")
                return games_list, response.status
    except asyncio.TimeoutError:
        return [], -1


@global_profiler.async_profiler
async def prepare_achiev(game_info, data, achievements_info):
    for a in data["achievements"]:
        for i in achievements_info:
            if a["achieved"] == 0 and a["apiname"] == i["name"]:
                field = {
                    "icon1": os.path.splitext(
                        os.path.basename(urlparse(i["icon"]).path)
                    )[0],
                    "icon2": os.path.splitext(
                        os.path.basename(urlparse(i["icongray"]).path)
                    )[0],
                    "name": i["displayName"],
                }
                if "description" in i:
                    field["desc"] = i["description"]

                game_info.achievements_info.append(field)


# @global_profiler.async_profiler
async def get_achievements_info(game_info, data, lang):
    achievements_cache_key = f"/achievements/{game_info.app_id}/{lang}"
    achievements_info = cache.get(achievements_cache_key)
    if not achievements_info:
        ach_list_result = await fetch_achievements_info(game_info.app_id, lang)
        achievements_info = ach_list_result["game"]["availableGameStats"][
            "achievements"
        ]
        cache.set(achievements_cache_key, achievements_info)

    game_info.achievements_done = sum(1 for a in data["achievements"] if a["achieved"])
    game_info.achievements_count = len(data["achievements"])
    game_info.title = data["gameName"]

    await prepare_achiev(game_info, data, achievements_info)

    return game_info


@global_profiler.async_profiler
async def prepare_game_info(steamid, lang, game_list):
    response = DefaultResponse()
    response.data = []

    overall_ach_count = 0
    overall_done_ach_count = 0

    async with aiohttp.ClientSession() as session:
        pending = []
        for game in game_list:
            payload = {
                "key": STEAM_SECRET_KEY,
                "appid": game["appid"],
                "steamid": steamid,
            }
            pending.append(
                asyncio.create_task(fetch_data(session, GAME_INFO_URL, payload))
            )

        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for done_task in done:
                result = await done_task
                try:
                    game_info = GameInfo()
                    game_info.app_id = result[1]["appid"]

                    await get_achievements_info(
                        game_info, result[0]["playerstats"], lang
                    )

                    response.data.append(game_info.serialize())

                    overall_ach_count += game_info.achievements_count
                    overall_done_ach_count += game_info.achievements_done
                except KeyError:
                    pass
                except Exception:
                    pass
    res = {
        "code": response.code,
        "status": response.status,
        "overall_done_ach_count": overall_done_ach_count,
        "overall_ach_count": overall_ach_count,
        "game_data": response.data,
    }
    return res


@app.route("/data/<steamid>")
@app.route("/data/<steamid>/<lang>")
async def index(steamid, lang="english"):
    steamid_cache_key = f"/data/{steamid}"

    data = cache.get(steamid_cache_key)
    response = DefaultResponse()
    if not data:
        games_list, response.code = await get_game_list(steamid)
        cache.set(steamid_cache_key, games_list)
    else:
        games_list = data
    if response.status:
        print("Start parsing games...")
        res = await prepare_game_info(steamid=steamid, lang=lang, game_list=games_list)
    else:
        res = {
            "code": response.code,
            "status": response.status,
            "message": response.message,
        }
    print(global_profiler.info)
    global_profiler.get_statistic()
    global_profiler.reset()
    return jsonify(res)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        pass
