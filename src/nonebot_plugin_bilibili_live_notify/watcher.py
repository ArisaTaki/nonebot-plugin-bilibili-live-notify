from __future__ import annotations

from typing import Any

from nonebot import get_bots, logger, on_type
from nonebot.adapters.bilibili_live import (
    OpenLiveEndEvent,
    OpenLiveStartEvent,
    StopLiveRoomListEvent,
    WebBot as BilibiliLiveWebBot,
    WebLiveStartEvent,
)
from nonebot.adapters.onebot.v11 import Bot as OneBotV11Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .adapter_state import resolve_monitored_room_id
from .runtime import store


async def _fetch_room_snapshot(
    bot: BilibiliLiveWebBot, room_id: int
) -> dict[str, str] | None:
    try:
        room = await bot.get_room_info(room_id)
    except Exception as e:
        logger.warning(
            "[bilibili_live_notify] failed to fetch room info room=%s: %s",
            room_id,
            e,
        )
        return None

    return {
        "title": room.title,
        "cover": room.user_cover or room.keyframe or "",
    }


def _pick_onebot_bot() -> OneBotV11Bot | None:
    for bot in get_bots().values():
        if isinstance(bot, OneBotV11Bot):
            return bot
    return None


async def send_notify(
    *,
    group_id: int,
    user_ids: list[int],
    room_id: int,
    title: str,
    remark: str,
    cover: str,
    is_live: bool,
) -> None:
    bot = _pick_onebot_bot()
    if bot is None:
        logger.error("[bilibili_live_notify] no onebot v11 bot available")
        return

    name = remark or title or f"直播间 {room_id}"
    link = f"https://live.bilibili.com/{room_id}"
    header = "【开播通知】" if is_live else "【下播通知】"
    body = f"{name} 已开播" if is_live else f"{name} 本场直播结束"

    msg = Message()
    if cover:
        msg.append(MessageSegment.image(cover))
    for user_id in user_ids:
        msg.append(MessageSegment.at(user_id))
    msg.append(MessageSegment.text(f"\n{header}\n{body}\n{link}"))

    try:
        await bot.send_group_msg(group_id=group_id, message=msg)
    except Exception as e:
        logger.warning(
            "[bilibili_live_notify] failed to send notify group=%s: %s",
            group_id,
            e,
        )


async def _get_room_subscription(room_id: int):
    room = store.get_room(room_id)
    if room is not None:
        return room_id, room

    for stored_room_id, stored_room in list(store.subs.rooms.items()):
        if resolve_monitored_room_id(stored_room_id) != room_id:
            continue

        store.subs.rooms[room_id] = stored_room
        store.subs.rooms.pop(stored_room_id, None)
        await store.save()
        logger.info(
            "[bilibili_live_notify] migrated stored room id %s -> %s",
            stored_room_id,
            room_id,
        )
        return room_id, stored_room

    return None, None


async def handle_room_state_change(
    *,
    room_id: int,
    is_live: bool,
    title: str = "",
    cover: str = "",
) -> None:
    canonical_room_id, room = await _get_room_subscription(room_id)
    if room is None or canonical_room_id is None or room.last_is_live == is_live:
        return

    logger.info(
        "[bilibili_live_notify] room %s state change: %s -> %s",
        canonical_room_id,
        room.last_is_live,
        is_live,
    )
    room.last_is_live = is_live
    await store.save()

    for group_id, group in room.groups.items():
        await send_notify(
            group_id=group_id,
            user_ids=group.participants,
            room_id=canonical_room_id,
            title=title,
            remark=room.remark,
            cover=cover,
            is_live=is_live,
        )


async def _resolve_room_payload(
    *,
    room_id: int,
    title: str = "",
    cover: str = "",
    snapshot: dict[str, str] | None = None,
) -> dict[str, Any]:
    snapshot = snapshot or {}
    return {
        "room_id": room_id,
        "title": title or snapshot.get("title", ""),
        "cover": cover or snapshot.get("cover", ""),
    }


live_start_web = on_type(WebLiveStartEvent, priority=10, block=False)
live_start_open = on_type(OpenLiveStartEvent, priority=10, block=False)
live_end_open = on_type(OpenLiveEndEvent, priority=10, block=False)
live_end_web = on_type(StopLiveRoomListEvent, priority=10, block=False)


@live_start_web.handle()
async def _handle_live_start_web(bot: BilibiliLiveWebBot, event: WebLiveStartEvent):
    snapshot = await _fetch_room_snapshot(bot, event.room_id)
    payload = await _resolve_room_payload(room_id=event.room_id, snapshot=snapshot)
    await handle_room_state_change(is_live=True, **payload)


@live_start_open.handle()
async def _handle_live_start_open(event: OpenLiveStartEvent):
    payload = await _resolve_room_payload(room_id=event.room_id, title=event.title)
    await handle_room_state_change(is_live=True, **payload)


@live_end_open.handle()
async def _handle_live_end_open(event: OpenLiveEndEvent):
    payload = await _resolve_room_payload(room_id=event.room_id, title=event.title)
    await handle_room_state_change(is_live=False, **payload)


@live_end_web.handle()
async def _handle_live_end_web(bot: BilibiliLiveWebBot, event: StopLiveRoomListEvent):
    for room_id in event.room_id_list:
        snapshot = await _fetch_room_snapshot(bot, room_id)
        payload = await _resolve_room_payload(room_id=room_id, snapshot=snapshot)
        await handle_room_state_change(is_live=False, **payload)
