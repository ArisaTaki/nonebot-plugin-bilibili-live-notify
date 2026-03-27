from __future__ import annotations

from pathlib import Path

import pytest

from nonebot_plugin_bilibili_live_notify.managed_rooms import ManagedRoomsStore


@pytest.mark.asyncio
async def test_managed_rooms_roundtrip(tmp_path: Path):
    managed = ManagedRoomsStore(tmp_path / "managed_rooms.json")
    assert await managed.add(12345) is True
    assert await managed.add(12345) is False

    reloaded = ManagedRoomsStore(tmp_path / "managed_rooms.json")
    assert reloaded.list() == [12345]
    assert await reloaded.remove(12345) is True
    assert reloaded.list() == []
