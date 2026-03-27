from __future__ import annotations

import asyncio
import json
from pathlib import Path

from nonebot import logger


class ManagedRoomsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.room_ids: list[int] = []
        self.storage_available = self._ensure_dirs()
        self.load()

    def _ensure_dirs(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(
                "[bilibili_live_notify] failed to prepare managed room dir %s: %s",
                self.path.parent,
                e,
            )
            return False
        return True

    def load(self) -> None:
        if not self.storage_available:
            self.room_ids = []
            return
        if not self.path.exists():
            self.room_ids = []
            return

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.room_ids = sorted({int(room_id) for room_id in data.get("room_ids", [])})
        except Exception as e:
            logger.error(
                "[bilibili_live_notify] failed to load managed rooms from %s: %s",
                self.path,
                e,
            )
            self.room_ids = []

    async def save(self) -> None:
        if not self.storage_available:
            return
        try:
            payload = json.dumps(
                {"room_ids": self.room_ids}, ensure_ascii=False, indent=2
            )
            await asyncio.to_thread(self.path.write_text, payload, encoding="utf-8")
        except Exception as e:
            logger.error(
                "[bilibili_live_notify] failed to save managed rooms to %s: %s",
                self.path,
                e,
            )

    async def add(self, room_id: int) -> bool:
        if room_id in self.room_ids:
            return False
        self.room_ids.append(room_id)
        self.room_ids.sort()
        await self.save()
        return True

    async def remove(self, room_id: int) -> bool:
        if room_id not in self.room_ids:
            return False
        self.room_ids.remove(room_id)
        await self.save()
        return True

    def list(self) -> list[int]:
        return list(self.room_ids)
