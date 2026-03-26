from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from nonebot import logger

# =========================
# 固定数据路径
# =========================
BASE_DIR = Path("/root/nonebot-docker/qqbot")
DATA_DIR = BASE_DIR / "data" / "bilibili_live_notify"
DATA_FILE = DATA_DIR / "subscriptions.json"


# =========================
# 数据结构
# =========================
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


# =========================
# Store 主体
# =========================
class Store:
    def __init__(self, path: Path = DATA_FILE) -> None:
        self.path = path
        self.subs = Subscriptions()
        self._ensure_dirs()
        self.load()

    # --------
    # 文件系统
    # --------
    def _ensure_dirs(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # --------
    # 序列化
    # --------
    def load(self) -> None:
        if not self.path.exists():
            logger.info("[bilibili_live_notify] no subscriptions.json, start fresh")
            self.subs = Subscriptions()
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.subs = self._from_dict(raw)
            logger.info(f"[bilibili_live_notify] loaded {len(self.subs.rooms)} rooms")
        except Exception as e:
            logger.error(f"[bilibili_live_notify] failed to load store: {e}")
            self.subs = Subscriptions()

    def save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self._to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"[bilibili_live_notify] failed to save store: {e}")

    # --------
    # JSON <-> 对象
    # --------
    def _to_dict(self) -> dict:
        return {
            "rooms": {
                str(room_id): {
                    "remark": room.remark,
                    "last_is_live": room.last_is_live,
                    "groups": {
                        str(group_id): {
                            "creator": group.creator,
                            "participants": group.participants,
                        }
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
                remark=room_data.get("remark", ""),
                last_is_live=room_data.get("last_is_live", False),
                groups={},
            )
            for group_id_str, group_data in room_data.get("groups", {}).items():
                room.groups[int(group_id_str)] = GroupSub(
                    creator=int(group_data["creator"]),
                    participants=list(map(int, group_data.get("participants", []))),
                )
            subs.rooms[int(room_id_str)] = room
        return subs

    # =========================
    # 业务接口
    # =========================

    def get_room(self, room_id: int) -> Optional[RoomSub]:
        return self.subs.rooms.get(room_id)

    def find_rooms_by_remark(self, remark: str) -> List[int]:
        return [
            room_id
            for room_id, room in self.subs.rooms.items()
            if room.remark == remark
        ]

    # ---- 订阅（不参与）----
    def subscribe_group(
        self,
        room_id: int,
        remark: str,
        group_id: int,
        creator_id: int,
    ) -> None:
        room = self.subs.rooms.get(room_id)
        if not room:
            room = RoomSub(remark=remark)
            self.subs.rooms[room_id] = room

        if group_id not in room.groups:
            room.groups[group_id] = GroupSub(
                creator=creator_id,
                participants=[],  # 管理员不默认参与
            )

        self.save()

    # ---- 参与 ----
    def add_participant(self, room_id: int, group_id: int, user_id: int) -> bool:
        room = self.subs.rooms.get(room_id)
        if not room:
            return False

        group = room.groups.get(group_id)
        if not group:
            return False

        group.ensure_participant(user_id)
        self.save()
        return True

    # ---- 退出参与 ----
    def remove_participant(self, room_id: int, group_id: int, user_id: int) -> bool:
        room = self.subs.rooms.get(room_id)
        if not room:
            return False

        group = room.groups.get(group_id)
        if not group:
            return False

        if user_id in group.participants:
            group.participants.remove(user_id)
            self.save()
            return True

        return False
