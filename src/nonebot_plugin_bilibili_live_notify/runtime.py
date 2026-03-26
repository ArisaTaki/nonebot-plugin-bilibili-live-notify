from __future__ import annotations

from pathlib import Path

import nonebot_plugin_localstore as localstore
from nonebot import logger

from .config import load_config
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


store = Store(get_store_path())
