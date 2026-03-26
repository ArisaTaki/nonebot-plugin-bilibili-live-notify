# nonebot-plugin-bilibili-live-notify

NoneBot2 的 Bilibili 直播订阅插件，支持在 QQ 群内订阅直播间，并在开播/下播时发送群通知，可按参与成员进行 `@` 提醒。

## 功能

- 群管理员订阅直播间
- 群成员自行加入或退出提醒名单
- 开播 / 下播自动推送
- 支持 `proxy`、`api`、`auto` 三种数据源模式
- 本地持久化订阅状态

## 前置要求

- NoneBot2
- OneBot V11 适配器
- 一个可访问的直播状态代理服务

本仓库内提供了兼容的 FastAPI 代理实现：`bilibili-proxy/main.py`。

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

推荐最小配置：

```env
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
```

完整配置项：

```env
BILIBILI_LIVE_NOTIFY_CHECK_INTERVAL=20
BILIBILI_LIVE_NOTIFY_REQUEST_TIMEOUT=10
BILIBILI_LIVE_NOTIFY_STARTUP_CHECK_DELAY=3
BILIBILI_LIVE_NOTIFY_DATA_FILE=data/bilibili_live_notify/subscriptions.json
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
BILIBILI_LIVE_NOTIFY_API_BASE=https://api.live.bilibili.com
```

- `BILIBILI_LIVE_NOTIFY_CHECK_INTERVAL`: 轮询间隔，默认 `20`
- `BILIBILI_LIVE_NOTIFY_REQUEST_TIMEOUT`: HTTP 请求超时，默认 `10`
- `BILIBILI_LIVE_NOTIFY_STARTUP_CHECK_DELAY`: 启动后首次检查前等待时间，默认 `3`
- `BILIBILI_LIVE_NOTIFY_DATA_FILE`: 数据存储文件路径
- `BILIBILI_LIVE_NOTIFY_SOURCE`: 数据来源，支持 `proxy`、`api`、`auto`，默认 `proxy`
- `BILIBILI_LIVE_NOTIFY_PROXY_URL`: 代理服务地址模板，需包含 `{room_id}`
- `BILIBILI_LIVE_NOTIFY_API_BASE`: 官方接口基础地址，仅 `api` 或 `auto` 模式使用

## 快速开始

1. 启动代理服务

```bash
uvicorn main:app --app-dir bilibili-proxy --host 127.0.0.1 --port 8000
```

2. 配置插件

```env
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
```

3. 在群内使用

```text
订阅直播 711308 狂肝无尽狂潮
参与直播 711308
直播订阅列表
```

## 指令

- `直播帮助`
- `订阅直播 <房间号> [备注]`
- `取消订阅直播 <房间号|备注>`
- `备注直播 <房间号|旧备注> <新备注>`
- `参与直播 <房间号|备注>`
- `取消参与直播 <房间号|备注>`
- `直播订阅列表`
- `我参与的直播`

## 代理服务协议

代理模式下，插件期望 HTTP 接口返回如下结构：

```json
{
  "ok": true,
  "room_id": 711308,
  "is_live": false,
  "live_status": 0,
  "title": "直播标题",
  "cover": "https://example.com/cover.jpg",
  "source": "html",
  "checked_at": 1774529586
}
```

## License

MIT
