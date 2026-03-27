from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS
from nonebot.adapters.onebot.v11 import Adapter


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def pytest_configure(config: pytest.Config):
    data_file = Path(tempfile.mkdtemp()) / "subscriptions.json"
    export_file = Path(tempfile.gettempdir()) / "generated_bilibili_live_bots.json"
    config.stash[NONEBOT_INIT_KWARGS] = {
        "superusers": {"123456"},
        "command_start": {"", "/"},
        "command_sep": {" "},
        "bilibili_live_notify_data_file": str(data_file),
        "bilibili_live_notify_export_file": str(export_file),
    }


@pytest.fixture(scope="session", autouse=True)
def register_adapter():
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)
