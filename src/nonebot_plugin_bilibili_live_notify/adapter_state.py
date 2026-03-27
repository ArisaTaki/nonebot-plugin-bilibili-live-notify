from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from nonebot import get_adapter, get_bots


def _iter_live_bots() -> Iterable[Any]:
    for bot in get_bots().values():
        if hasattr(bot, "rooms") or hasattr(bot, "games"):
            yield bot


def iter_web_live_bots() -> Iterable[Any]:
    for bot in _iter_live_bots():
        rooms = getattr(bot, "rooms", {})
        cookie = getattr(bot, "cookie", None)
        if isinstance(rooms, dict) and isinstance(cookie, dict):
            yield bot


def resolve_monitored_room_id(room_id: int) -> int | None:
    for bot in _iter_live_bots():
        rooms = getattr(bot, "rooms", {})
        if not isinstance(rooms, dict):
            rooms = {}
        for monitored_room in rooms.values():
            long_room_id = getattr(monitored_room, "room_id", None)
            short_room_id = getattr(monitored_room, "short_id", None)
            if room_id in {long_room_id, short_room_id}:
                return long_room_id

        games = getattr(bot, "games", {})
        if not isinstance(games, dict):
            games = {}
        for monitored_game in games.values():
            long_room_id = getattr(monitored_game, "room_id", None)
            if room_id == long_room_id:
                return long_room_id

    return None


def is_room_monitored(room_id: int) -> bool:
    return resolve_monitored_room_id(room_id) is not None


def dump_cookie(cookie: dict[str, Any]) -> str:
    return "; ".join(f"{key}={value}" for key, value in cookie.items())


_scheduled_room_ids: set[int] = set()


def schedule_web_room_monitor(room_id: int) -> tuple[bool, str]:
    if is_room_monitored(room_id):
        return True, f"房间 {room_id} 已在当前适配器中监听"

    if room_id in _scheduled_room_ids:
        return True, f"房间 {room_id} 已加入本次运行的监听队列"

    web_bots = list(iter_web_live_bots())
    if not web_bots:
        return False, "当前没有可用的 bilibili-live Web Bot，无法自动补挂监听"

    try:
        from nonebot.adapters.bilibili_live import Adapter as BilibiliLiveAdapter

        adapter = get_adapter(BilibiliLiveAdapter)
    except ValueError:
        return False, "当前未加载 bilibili-live 适配器，无法自动补挂监听"

    if not hasattr(adapter, "_listen_room_web") or not hasattr(adapter, "tasks"):
        return False, "当前 bilibili-live 适配器版本不支持自动补挂监听"

    bot = web_bots[0]
    task = asyncio.create_task(adapter._listen_room_web(bot, room_id))
    adapter.tasks.add(task)
    task.add_done_callback(adapter.tasks.discard)
    _scheduled_room_ids.add(room_id)

    def _cleanup(_: asyncio.Task[Any]) -> None:
        if not is_room_monitored(room_id):
            _scheduled_room_ids.discard(room_id)

    task.add_done_callback(_cleanup)
    return True, f"房间 {room_id} 已加入当前进程的监听任务"
