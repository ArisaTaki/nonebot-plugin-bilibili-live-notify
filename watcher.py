from __future__ import annotations

import asyncio
from typing import Dict, Any

import httpx
from nonebot import get_bot, get_driver, logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot_plugin_apscheduler import scheduler

from .store import Store

# =========================
# 配置
# =========================
CHECK_INTERVAL = 20  # 秒
FASTAPI_ENDPOINT = "http://8.134.250.180:8000/bilibili/live?room_id={room_id}"

store = Store()
driver = get_driver()

# =========================
# 获取直播状态（FastAPI）
# =========================
async def fetch_live_status(room_id: int) -> Dict[str, Any] | None:
    url = FASTAPI_ENDPOINT.format(room_id=room_id)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(
            f"[bilibili_live_notify] fetch failed room={room_id}: {e}"
        )
        return None


# =========================
# 发送通知（始终推送，按需 @）
# =========================
async def send_notify(
    *,
    group_id: int,
    user_ids: list[int],
    room_id: int,
    title: str,
    remark: str,
    cover: str,
    is_live: bool,
):
    try:
        bot = get_bot()
    except Exception:
        logger.error("[bilibili_live_notify] no bot available")
        return

    name = remark or title or f"直播间 {room_id}"
    link = f"https://live.bilibili.com/{room_id}"

    if is_live:
        header = "📢【开播通知】"
        body = f"{name} 已开播"
    else:
        header = "📴【下播通知】"
        body = f"{name} 本场直播结束"

    msg = Message()

    # 1️⃣ 封面
    if cover:
        msg.append(MessageSegment.image(cover))

    # 2️⃣ @ 参与者（如果有）
    for uid in user_ids:
        msg.append(MessageSegment.at(uid))

    # 3️⃣ 文案 + 链接
    msg.append(
        MessageSegment.text(
            f"\n{header}\n"
            f"{body}\n"
            f"{link}"
        )
    )

    await bot.send_group_msg(group_id=group_id, message=msg)


# =========================
# 核心检测逻辑
# =========================
async def check_all_rooms():
    if not store.subs.rooms:
        return

    logger.info("[bilibili_live_notify] checking live status")

    for room_id, room in store.subs.rooms.items():
        data = await fetch_live_status(room_id)
        if not data or not data.get("ok"):
            continue

        is_live_now = bool(data.get("is_live"))
        title = data.get("title", "")
        cover = data.get("cover", "")

        # 状态未变化 → 不推送
        if room.last_is_live == is_live_now:
            continue

        logger.info(
            f"[bilibili_live_notify] room {room_id} state change: "
            f"{room.last_is_live} -> {is_live_now}"
        )

        # 更新状态
        room.last_is_live = is_live_now
        store.save()

        # 群订阅了一定推送（是否 @ 由 participants 决定）
        for group_id, group in room.groups.items():
            await send_notify(
                group_id=group_id,
                user_ids=group.participants,  # 允许为空
                room_id=room_id,
                title=title,
                remark=room.remark,
                cover=cover,
                is_live=is_live_now,
            )


# =========================
# 定时任务（⚠️ 不要 replace_existing）
# =========================
@scheduler.scheduled_job(
    "interval",
    seconds=CHECK_INTERVAL,
    id="bilibili_live_check",
)
async def live_check_job():
    await check_all_rooms()


# =========================
# 启动即检查一次（防重启漏状态）
# =========================
@driver.on_startup
async def startup_check():
    logger.info("[bilibili_live_notify] startup check")
    await asyncio.sleep(3)
    await check_all_rooms()
