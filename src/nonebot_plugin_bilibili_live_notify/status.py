from __future__ import annotations

from typing import Any

from nonebot import logger


def normalize_proxy_payload(payload: dict[str, Any], room_id: int) -> dict[str, Any] | None:
    if not payload.get("ok"):
        logger.warning(
            "[bilibili_live_notify] proxy returned not ok room=%s payload=%s",
            room_id,
            payload,
        )
        return None

    return {
        "ok": True,
        "is_live": bool(payload.get("is_live")),
        "title": str(payload.get("title") or ""),
        "cover": str(payload.get("cover") or ""),
    }


def normalize_api_payload(payload: dict[str, Any], room_id: int) -> dict[str, Any] | None:
    if payload.get("code") != 0:
        logger.warning(
            "[bilibili_live_notify] bilibili api error room=%s code=%s message=%s",
            room_id,
            payload.get("code"),
            payload.get("message"),
        )
        return None

    data = payload.get("data") or {}
    return {
        "ok": True,
        "is_live": data.get("live_status") == 1,
        "title": str(data.get("title") or ""),
        "cover": str(data.get("user_cover") or data.get("keyframe") or ""),
    }
