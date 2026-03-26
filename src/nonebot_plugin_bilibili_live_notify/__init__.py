from nonebot import get_driver, require
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Bilibili Live Notify",
    description="在 QQ 群内订阅 B 站直播间并推送开播/下播通知。",
    usage=(
        "订阅直播 <房间号> [备注]\n"
        "取消订阅直播 <房间号|备注>\n"
        "备注直播 <房间号|旧备注> <新备注>\n"
        "参与直播 <房间号|备注>\n"
        "取消参与直播 <房间号|备注>\n"
        "直播订阅列表\n"
        "我参与的直播"
    ),
    type="application",
    homepage="https://pypi.org/project/nonebot-plugin-bilibili-live-notify/",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

try:
    get_driver()
except ValueError:
    commands = None
    watcher = None
else:
    require("nonebot_plugin_apscheduler")
    from . import commands as commands
    from . import watcher as watcher

__all__ = ["__plugin_meta__", "commands", "watcher"]
