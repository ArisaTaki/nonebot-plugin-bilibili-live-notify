from __future__ import annotations

from nonebot_plugin_bilibili_live_notify.status import (
    normalize_api_payload,
    normalize_proxy_payload,
)


def test_normalize_proxy_payload():
    payload = {
        "ok": True,
        "room_id": 711308,
        "is_live": False,
        "live_status": 0,
        "title": "测试标题",
        "cover": "https://example.com/cover.jpg",
        "source": "html",
        "checked_at": 1774529586,
    }

    assert normalize_proxy_payload(payload, 711308) == {
        "ok": True,
        "is_live": False,
        "title": "测试标题",
        "cover": "https://example.com/cover.jpg",
    }


def test_normalize_api_payload():
    payload = {
        "code": 0,
        "data": {
            "live_status": 1,
            "title": "官方接口标题",
            "user_cover": "https://example.com/api-cover.jpg",
        },
    }

    assert normalize_api_payload(payload, 711308) == {
        "ok": True,
        "is_live": True,
        "title": "官方接口标题",
        "cover": "https://example.com/api-cover.jpg",
    }
