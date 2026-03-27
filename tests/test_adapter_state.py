from __future__ import annotations

from types import SimpleNamespace

from nonebot_plugin_bilibili_live_notify import adapter_state


def test_resolve_monitored_room_id_from_web_room(monkeypatch):
    room = SimpleNamespace(room_id=711308, short_id=12345)
    bot = SimpleNamespace(rooms={711308: room}, games={})
    monkeypatch.setattr(adapter_state, "get_bots", lambda: {"live": bot})

    assert adapter_state.resolve_monitored_room_id(711308) == 711308
    assert adapter_state.resolve_monitored_room_id(12345) == 711308


def test_resolve_monitored_room_id_from_open_game(monkeypatch):
    game = SimpleNamespace(room_id=888888)
    bot = SimpleNamespace(rooms={}, games={888888: game})
    monkeypatch.setattr(adapter_state, "get_bots", lambda: {"live": bot})

    assert adapter_state.resolve_monitored_room_id(888888) == 888888
