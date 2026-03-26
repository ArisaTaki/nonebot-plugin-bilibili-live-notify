from __future__ import annotations

import asyncio
from typing import Any

import httpx
from nonebot import get_bots, get_driver, logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from .runtime import plugin_config, store
from .status import normalize_api_payload, normalize_proxy_payload

driver = get_driver()


async def _fetch_via_proxy(room_id: int) -> dict[str, Any] | None:
    url = plugin_config.proxy_url.format(room_id=room_id)
    try:
        async with httpx.AsyncClient(timeout=plugin_config.request_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logger.warning(f"[bilibili_live_notify] proxy fetch failed room={room_id}: {e}")
        return None

    return normalize_proxy_payload(payload, room_id)


async def _fetch_via_api(room_id: int) -> dict[str, Any] | None:
    url = f"{plugin_config.api_base}/room/v1/Room/get_info"
    params = {"room_id": room_id}
    try:
        async with httpx.AsyncClient(timeout=plugin_config.request_timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logger.warning(f"[bilibili_live_notify] api fetch failed room={room_id}: {e}")
        return None

    return normalize_api_payload(payload, room_id)


async def fetch_live_status(room_id: int) -> dict[str, Any] | None:
    source = plugin_config.source

    if source == "proxy":
        return await _fetch_via_proxy(room_id)

    if source == "api":
        return await _fetch_via_api(room_id)

    if source == "auto":
        data = await _fetch_via_proxy(room_id)
        if data is not None:
            return data
        logger.warning(
            "[bilibili_live_notify] proxy unavailable for room=%s, fallback to api",
            room_id,
        )
        return await _fetch_via_api(room_id)

    logger.warning(
        "[bilibili_live_notify] invalid source=%s, expected proxy/api/auto",
        source,
    )
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
    bots = get_bots()
    if not bots:
        logger.error("[bilibili_live_notify] no bot available")
        return

    bot = next(iter(bots.values()))
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
            f"[bilibili_live_notify] failed to send notify group={group_id}: {e}"
        )


async def check_all_rooms() -> None:
    if not store.subs.rooms:
        return

    logger.info("[bilibili_live_notify] checking live status")

    for room_id, room in list(store.subs.rooms.items()):
        data = await fetch_live_status(room_id)
        if not data or not data.get("ok"):
            continue

        is_live_now = bool(data.get("is_live"))
        if room.last_is_live == is_live_now:
            continue

        logger.info(
            f"[bilibili_live_notify] room {room_id} state change: "
            f"{room.last_is_live} -> {is_live_now}"
        )
        room.last_is_live = is_live_now
        store.save()

        for group_id, group in room.groups.items():
            await send_notify(
                group_id=group_id,
                user_ids=group.participants,
                room_id=room_id,
                title=str(data.get("title") or ""),
                remark=room.remark,
                cover=str(data.get("cover") or ""),
                is_live=is_live_now,
            )


@scheduler.scheduled_job(
    "interval",
    seconds=plugin_config.check_interval,
    id="bilibili_live_notify_check",
    replace_existing=True,
)
async def live_check_job() -> None:
    await check_all_rooms()


@driver.on_startup
async def startup_check() -> None:
    logger.info("[bilibili_live_notify] startup check")
    await asyncio.sleep(plugin_config.startup_check_delay)
    await check_all_rooms()
