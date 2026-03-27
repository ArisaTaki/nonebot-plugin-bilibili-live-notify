from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from nonebot import logger


@dataclass
class GroupSub:
    creator: int
    participants: List[int] = field(default_factory=list)

    def ensure_participant(self, user_id: int) -> None:
        if user_id not in self.participants:
            self.participants.append(user_id)


@dataclass
class RoomSub:
    remark: str
    last_is_live: bool = False
    groups: Dict[int, GroupSub] = field(default_factory=dict)


@dataclass
class Subscriptions:
    rooms: Dict[int, RoomSub] = field(default_factory=dict)


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.subs = Subscriptions()
        self.storage_available = self._ensure_dirs()
        self.load()

    def _ensure_dirs(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(
                f"[bilibili_live_notify] failed to prepare store dir {self.path.parent}: {e}"
            )
            return False
        return True

    def load(self) -> None:
        if not self.storage_available:
            logger.warning(
                "[bilibili_live_notify] storage unavailable, use in-memory subscriptions"
            )
            self.subs = Subscriptions()
            return

        if not self.path.exists():
            logger.info("[bilibili_live_notify] no subscriptions file, start fresh")
            self.subs = Subscriptions()
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.subs = self._from_dict(raw)
            logger.info(f"[bilibili_live_notify] loaded {len(self.subs.rooms)} rooms")
        except Exception as e:
            logger.error(f"[bilibili_live_notify] failed to load store: {e}")
            self.subs = Subscriptions()

    async def save(self) -> None:
        if not self.storage_available:
            logger.warning(
                "[bilibili_live_notify] skip saving because storage is unavailable"
            )
            return
        try:
            payload = json.dumps(self._to_dict(), ensure_ascii=False, indent=2)
            await asyncio.to_thread(self.path.write_text, payload, encoding="utf-8")
        except Exception as e:
            logger.error(f"[bilibili_live_notify] failed to save store: {e}")

    def _to_dict(self) -> dict:
        return {
            "rooms": {
                str(room_id): {
                    "remark": room.remark,
                    "last_is_live": room.last_is_live,
                    "groups": {
                        str(group_id): asdict(group)
                        for group_id, group in room.groups.items()
                    },
                }
                for room_id, room in self.subs.rooms.items()
            }
        }

    def _from_dict(self, data: dict) -> Subscriptions:
        subs = Subscriptions()
        for room_id_str, room_data in data.get("rooms", {}).items():
            room = RoomSub(
                remark=room_data.get("remark", room_id_str),
                last_is_live=bool(room_data.get("last_is_live", False)),
                groups={},
            )
            for group_id_str, group_data in room_data.get("groups", {}).items():
                room.groups[int(group_id_str)] = GroupSub(
                    creator=int(group_data["creator"]),
                    participants=[int(uid) for uid in group_data.get("participants", [])],
                )
            subs.rooms[int(room_id_str)] = room
        return subs

    def get_room(self, room_id: int) -> Optional[RoomSub]:
        return self.subs.rooms.get(room_id)

    def find_rooms_by_remark(self, remark: str) -> List[int]:
        return [
            room_id
            for room_id, room in self.subs.rooms.items()
            if room.remark == remark
        ]

    async def subscribe_group(
        self,
        room_id: int,
        remark: str,
        group_id: int,
        creator_id: int,
    ) -> None:
        room = self.subs.rooms.get(room_id)
        if room is None:
            room = RoomSub(remark=remark)
            self.subs.rooms[room_id] = room
        else:
            room.remark = remark or room.remark

        if group_id not in room.groups:
            room.groups[group_id] = GroupSub(creator=creator_id)

        await self.save()

    async def unsubscribe_group(self, room_id: int, group_id: int) -> bool:
        room = self.subs.rooms.get(room_id)
        if room is None or group_id not in room.groups:
            return False

        room.groups.pop(group_id, None)
        if not room.groups:
            self.subs.rooms.pop(room_id, None)
        await self.save()
        return True

    async def rename_room(self, room_id: int, remark: str) -> bool:
        room = self.subs.rooms.get(room_id)
        if room is None:
            return False

        room.remark = remark
        await self.save()
        return True

    async def add_participant(self, room_id: int, group_id: int, user_id: int) -> bool:
        room = self.subs.rooms.get(room_id)
        if room is None:
            return False

        group = room.groups.get(group_id)
        if group is None:
            return False

        group.ensure_participant(user_id)
        await self.save()
        return True

    async def remove_participant(self, room_id: int, group_id: int, user_id: int) -> bool:
        room = self.subs.rooms.get(room_id)
        if room is None:
            return False

        group = room.groups.get(group_id)
        if group is None or user_id not in group.participants:
            return False

        group.participants.remove(user_id)
        await self.save()
        return True
