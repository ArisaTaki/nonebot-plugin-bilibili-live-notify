from __future__ import annotations

from pathlib import Path
from typing import Any

from nonebot import get_driver
from pydantic import BaseModel, Field


class Config(BaseModel):
    bilibili_live_notify_check_interval: int = Field(default=20, ge=5)
    bilibili_live_notify_request_timeout: float = Field(default=10.0, gt=0)
    bilibili_live_notify_startup_check_delay: float = Field(default=3.0, ge=0)
    bilibili_live_notify_data_file: str = "data/bilibili_live_notify/subscriptions.json"
    bilibili_live_notify_source: str = "proxy"
    bilibili_live_notify_api_base: str = "https://api.live.bilibili.com"
    bilibili_live_notify_proxy_url: str = (
        "http://127.0.0.1:8000/bilibili/live?room_id={room_id}"
    )

    @property
    def check_interval(self) -> int:
        return self.bilibili_live_notify_check_interval

    @property
    def request_timeout(self) -> float:
        return self.bilibili_live_notify_request_timeout

    @property
    def startup_check_delay(self) -> float:
        return self.bilibili_live_notify_startup_check_delay

    @property
    def data_file(self) -> Path:
        return Path(self.bilibili_live_notify_data_file).expanduser()

    @property
    def api_base(self) -> str:
        return self.bilibili_live_notify_api_base.rstrip("/")

    @property
    def source(self) -> str:
        return self.bilibili_live_notify_source.strip().lower()

    @property
    def proxy_url(self) -> str:
        return self.bilibili_live_notify_proxy_url


def _model_validate(data: dict[str, Any]) -> Config:
    if hasattr(Config, "model_validate"):
        return Config.model_validate(data)
    return Config.parse_obj(data)


def load_config() -> Config:
    raw_config = get_driver().config
    field_names = getattr(Config, "model_fields", None)
    if field_names is None:
        field_names = getattr(Config, "__fields__", {})

    data = {
        field_name: getattr(raw_config, field_name)
        for field_name in field_names
        if hasattr(raw_config, field_name)
    }
    return _model_validate(data)
