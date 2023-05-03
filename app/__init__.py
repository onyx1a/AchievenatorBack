from urllib.parse import urlparse

import os
import asyncio
import aiohttp

from flask import Flask, jsonify
from flask_caching import Cache

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
                    print(f"Found {len(games_list)} games in {prof.elapsed}s")
                    success = True
                else:
                    success = False
                return games_list, success, response.status
    except asyncio.TimeoutError:
        return [], False, -1


@app.route("/data/<steamid>")
@app.route("/data/<steamid>/<lang>")
async def index(steamid, lang="english"):
    steamid_cache_key = f"/data/{steamid}"
@global_profiler.async_profiler
async def get_achievements_info(game_info, data, lang):
@global_profiler.async_profiler
async def prepare_game_info(steamid, lang, game_list):

    data = cache.get(steamid_cache_key)
    if not data:
        games_list, status, code = await get_game_list(steamid)
        cache.set(steamid_cache_key, games_list)
    else:
        status = True
        code = 200
        games_list = data
    info_list = []
    overall_ach_count = 0
    overall_done_ach_count = 0
    print("Start parsing games...")
    prof = Profiler()
    async with aiohttp.ClientSession() as session:
        pending = []
        for game in games_list:
            payload = {"key": STEAM_SECRET_KEY, "appid": game["appid"], "steamid": steamid}
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
                    data = result[0]["playerstats"]
                    app_id = result[1]["appid"]
                    done_achievements = sum(
                        1
                        for achievement_data in data["achievements"]
                        if achievement_data["achieved"] == 1
                    )

                    achievements_cache_key = f"/achievements/{app_id}/{lang}"
                    achievements_info = cache.get(achievements_cache_key)
                    if not achievements_info:
                        ach_list_result = await get_achievements_info(app_id, lang)
                        achievements_info = ach_list_result["game"][
                            "availableGameStats"
                        ]["achievements"]
                        cache.set(achievements_cache_key, achievements_info)

                    ach_list = [
                        i
                        for i in achievements_info
                        if any(
                            a["apiname"] == i["name"]
                            for a in data["achievements"]
                            if a["achieved"] == 0
                        )
                    ]

                    for item in achievements_info:
                        icon_url = item["icon"]
                        icongray_url = item["icongray"]
                        item["icon"] = os.path.splitext(
                            os.path.basename(urlparse(icon_url).path)
                        )[0]
                        item["icongray"] = os.path.splitext(
                            os.path.basename(urlparse(icongray_url).path)
                        )[0]
                        del item["defaultvalue"]
                        del item["hidden"]
                        del item["name"]

                    game_info = GameInfo(
                        app_id,
                        data["gameName"],
                        len(data["achievements"]),
                        done_achievements,
                        ach_list,
                    )
                    info_list.append(game_info.serialize())
                    overall_ach_count += game_info.achievements_count
                    overall_done_ach_count += game_info.achievements_done
                except KeyError:
                    pass
                except Exception as ex:
                    print(ex)
    print("Done in", prof.elapsed)
    return jsonify(
        {
            "code": code,
            "status": status,
            "overall_done_ach_count": overall_done_ach_count,
            "overall_ach_count": overall_ach_count,
            "game_data": info_list,
        }
    )
    print(global_profiler.info)
    global_profiler.reset()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        pass
