from __future__ import annotations

from pathlib import Path

import nonebot_plugin_localstore as localstore

from .config import load_config
from .store import Store


plugin_config = load_config()


def get_store_path() -> Path:
    if plugin_config.data_file is not None:
        return plugin_config.data_file
    return localstore.get_plugin_data_file("subscriptions.json")


store = Store(get_store_path())
