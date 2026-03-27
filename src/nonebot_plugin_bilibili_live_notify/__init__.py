from nonebot import get_driver, logger, require
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Bilibili Live Notify",
    description="基于 bilibili-live 适配器的 QQ 群 B 站直播订阅与报名提醒插件。",
    usage=(
        "订阅直播 <房间号> [备注]\n"
        "取消订阅直播 <房间号|备注>\n"
        "备注直播 <房间号|旧备注> <新备注>\n"
        "直播监听列表\n"
        "导出直播监听配置\n"
        "参与直播 <房间号|备注>\n"
        "取消参与直播 <房间号|备注>\n"
        "直播订阅列表\n"
        "我参与的直播"
    ),
    type="application",
    homepage="https://github.com/ArisaTaki/nonebot-plugin-bilibili-live-notify",
    config=Config,
    supported_adapters={"~onebot.v11", "~bilibili_live"},
)

try:
    get_driver()
except ValueError:
    commands = None
    watcher = None
else:
    require("nonebot_plugin_localstore")
    from . import commands as commands
    try:
        from . import watcher as watcher
    except ModuleNotFoundError as e:
        if e.name != "nonebot.adapters.bilibili_live":
            raise
        logger.warning(
            "[bilibili_live_notify] bilibili-live adapter is not installed, "
            "event watcher disabled"
        )
        watcher = None

__all__ = ["__plugin_meta__", "commands", "watcher"]
