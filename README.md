# nonebot-plugin-bilibili-live-notify

基于 `nonebot-adapter-bilibili-live` 的 NoneBot2 插件，专注于 QQ 群内的 B 站直播订阅管理：

- 群管理员订阅直播间
- 群成员自行加入或退出提醒名单
- 开播 / 下播自动推送
- 按参与成员进行 `@` 提醒
- 本地持久化订阅状态

直接消费 `nonebot-adapter-bilibili-live` 提供的直播事件。

## 前置要求

- NoneBot2 `>= 2.4.2`
- `nonebot-adapter-onebot`
- `nonebot-adapter-bilibili-live`

推荐使用 `bilibili-live` 适配器的 Web Bot 模式，因为可以直接按房间号监听。

## 安装

使用 `nb` 安装：

```bash
nb plugin install nonebot-plugin-bilibili-live-notify
```

或使用 `pip` 安装：

```bash
pip install nonebot-plugin-bilibili-live-notify
```

然后在 NoneBot 中加载插件：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_bilibili_live_notify"]
```

## 配置

插件自身只需要一个可选配置项：

```env
BILIBILI_LIVE_NOTIFY_DATA_FILE=.data/nonebot_plugin_bilibili_live_notify/subscriptions.json
BILIBILI_LIVE_NOTIFY_MANAGED_ROOMS_FILE=.data/nonebot_plugin_bilibili_live_notify/managed_rooms.json
BILIBILI_LIVE_NOTIFY_EXPORT_FILE=.data/nonebot_plugin_bilibili_live_notify/generated_bilibili_live_bots.json
```

- `BILIBILI_LIVE_NOTIFY_DATA_FILE`: 自定义订阅数据文件路径；默认由 `nonebot-plugin-localstore` 管理
- `BILIBILI_LIVE_NOTIFY_MANAGED_ROOMS_FILE`: 维护待监听房间列表的文件路径
- `BILIBILI_LIVE_NOTIFY_EXPORT_FILE`: 导出的 `BILIBILI_LIVE_BOTS` 配置文件路径

直播事件来源由 `nonebot-adapter-bilibili-live` 提供，你还需要配置它的 `BILIBILI_LIVE_BOTS`。

Web Bot 示例：

```env
DRIVER=~httpx+~websockets
BILIBILI_LIVE_BOTS='
[
  {
    "cookie": "SESSDATA=xxxxxxxxxxxxxxxx; bili_jct=xxxxxxxxxxxxx;",
    "room_ids": [711308, 12345]
  }
]
'
```

## 使用说明

在群内使用：

```text
订阅直播 711308 狂肝无尽狂潮
参与直播 711308
直播订阅列表
```

支持指令：

- `直播帮助`
- `订阅直播 <房间号> [备注]`
- `取消订阅直播 <房间号|备注>`
- `备注直播 <房间号|旧备注> <新备注>`
- `直播监听列表`
- `更新直播监听配置`
- `导出直播监听配置`
- `参与直播 <房间号|备注>`
- `取消参与直播 <房间号|备注>`
- `直播订阅列表`
- `我参与的直播`

## 重要说明

`nonebot-adapter-bilibili-live` 静态监听房间配置，本插件会额外维护一份“待监听房间列表”：

1. 群里执行 `订阅直播` 时，如果该房间尚未被适配器监听，插件会自动把它加入待监听列表。
2. 插件会立刻尝试在当前进程里补挂监听，并自动刷新导出的适配器配置文件。
3. 管理员通常只需要正常订阅；只有在想检查状态时再用 `直播监听列表`，或在自动补挂失败时手动执行 `更新直播监听配置`。
4. 如果希望下次重启后仍然保留这些房间，再将自动导出的文件内容同步到 `BILIBILI_LIVE_BOTS`。

说明：

- 为了避免在群消息里直接暴露 Cookie，插件会把导出结果写到本地文件，而不是直接回显完整配置。
- 当前默认会把“待监听房间”并入第一个可用的 `bilibili-live` Web Bot 配置中。
- `更新直播监听配置` 依赖适配器内部实现做运行时补挂，适合提升使用体验；真正的长期持久化仍以导出后的 `BILIBILI_LIVE_BOTS` 为准。
- 插件在订阅和取消订阅后都会自动刷新导出文件，因此通常不需要再手动执行 `导出直播监听配置`。

## 定位

`nonebot-adapter-bilibili-live` 负责“监听直播事件”。

本插件负责“群订阅管理、成员报名、按参与名单提醒、下播通知、持久化”。

## License

MIT
