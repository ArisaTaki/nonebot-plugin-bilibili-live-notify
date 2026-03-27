from __future__ import annotations

from pathlib import Path

import nonebot_plugin_localstore as localstore
from nonebot import logger

from .config import load_config
from .managed_rooms import ManagedRoomsStore
from .store import Store


plugin_config = load_config()


def get_store_path() -> Path:
    if plugin_config.data_file is not None:
        return plugin_config.data_file
    try:
        return localstore.get_plugin_data_file("subscriptions.json")
    except Exception as e:
        fallback = Path(".data/nonebot_plugin_bilibili_live_notify/subscriptions.json")
        logger.warning(
            f"[bilibili_live_notify] failed to get localstore path, fallback to {fallback}: {e}"
        )
        return fallback


def get_managed_rooms_path() -> Path:
    if plugin_config.managed_rooms_file is not None:
        return plugin_config.managed_rooms_file
    try:
        return localstore.get_plugin_data_file("managed_rooms.json")
    except Exception as e:
        fallback = Path(".data/nonebot_plugin_bilibili_live_notify/managed_rooms.json")
        logger.warning(
            f"[bilibili_live_notify] failed to get managed room path, fallback to {fallback}: {e}"
        )
        return fallback


def get_export_path() -> Path:
    if plugin_config.export_file is not None:
        return plugin_config.export_file
    try:
        return localstore.get_plugin_data_file("generated_bilibili_live_bots.json")
    except Exception as e:
        fallback = Path(
            ".data/nonebot_plugin_bilibili_live_notify/generated_bilibili_live_bots.json"
        )
        logger.warning(
            f"[bilibili_live_notify] failed to get export path, fallback to {fallback}: {e}"
        )
        return fallback


store = Store(get_store_path())
managed_rooms = ManagedRoomsStore(get_managed_rooms_path())
export_path = get_export_path()
