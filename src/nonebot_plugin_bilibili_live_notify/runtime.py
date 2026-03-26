from __future__ import annotations

from .config import load_config
from .store import Store


plugin_config = load_config()
store = Store(plugin_config.data_file)
