from __future__ import annotations

from pathlib import Path

from nonebot_plugin_bilibili_live_notify.store import Store


def test_store_roundtrip(tmp_path: Path):
    store = Store(tmp_path / "subscriptions.json")
    store.subscribe_group(room_id=123, remark="测试主播", group_id=456, creator_id=789)
    assert store.add_participant(123, 456, 10001) is True

    reloaded = Store(tmp_path / "subscriptions.json")
    room = reloaded.get_room(123)

    assert room is not None
    assert room.remark == "测试主播"
    assert room.groups[456].creator == 789
    assert room.groups[456].participants == [10001]


def test_unsubscribe_last_group_removes_room(tmp_path: Path):
    store = Store(tmp_path / "subscriptions.json")
    store.subscribe_group(room_id=123, remark="测试主播", group_id=456, creator_id=789)

    assert store.unsubscribe_group(123, 456) is True
    assert store.get_room(123) is None
