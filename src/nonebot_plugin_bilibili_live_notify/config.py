from __future__ import annotations

from pathlib import Path
from typing import Any

from nonebot import get_driver
from pydantic import BaseModel


class Config(BaseModel):
    bilibili_live_notify_data_file: str | None = None
    bilibili_live_notify_managed_rooms_file: str | None = None
    bilibili_live_notify_export_file: str | None = None

    @property
    def data_file(self) -> Path | None:
        if not self.bilibili_live_notify_data_file:
            return None
        return Path(self.bilibili_live_notify_data_file).expanduser()

    @property
    def managed_rooms_file(self) -> Path | None:
        if not self.bilibili_live_notify_managed_rooms_file:
            return None
        return Path(self.bilibili_live_notify_managed_rooms_file).expanduser()

    @property
    def export_file(self) -> Path | None:
        if not self.bilibili_live_notify_export_file:
            return None
        return Path(self.bilibili_live_notify_export_file).expanduser()


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
