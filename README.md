# nonebot-plugin-bilibili-live-notify

用于 NoneBot2 的 Bilibili 直播订阅插件，支持在 QQ 群内订阅直播间，并在开播/下播时发送群通知，可按群成员维度进行 `@` 提醒。

这个插件默认依赖一个可访问的直播状态代理服务。仓库内提供了兼容的 FastAPI 实现，适合自部署。

## 功能

- 管理员按群订阅直播间
- 群成员自行加入或退出提醒名单
- 支持通过自定义 FastAPI 代理服务获取直播状态
- 可选直连 Bilibili 官方接口，或在 `auto` 模式下自动降级
- 本地持久化订阅状态

## 安装

```bash
pip install nonebot-plugin-bilibili-live-notify
```

在 `pyproject.toml` 中启用插件：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_bilibili_live_notify"]
```

## 快速开始

1. 启动代理服务

```bash
uvicorn main:app --app-dir bilibili-proxy --host 127.0.0.1 --port 8000
```

2. 在 NoneBot 配置中添加：

```env
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
```

3. 在群内使用：

```text
订阅直播 711308 狂肝无尽狂潮
参与直播 711308
直播订阅列表
```

## 配置

可通过 NoneBot 全局配置项覆盖默认值：

```env
BILIBILI_LIVE_NOTIFY_CHECK_INTERVAL=20
BILIBILI_LIVE_NOTIFY_REQUEST_TIMEOUT=10
BILIBILI_LIVE_NOTIFY_STARTUP_CHECK_DELAY=3
BILIBILI_LIVE_NOTIFY_DATA_FILE=data/bilibili_live_notify/subscriptions.json
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
BILIBILI_LIVE_NOTIFY_API_BASE=https://api.live.bilibili.com
```

配置说明：

- `BILIBILI_LIVE_NOTIFY_CHECK_INTERVAL`: 轮询间隔，单位秒，默认 `20`
- `BILIBILI_LIVE_NOTIFY_REQUEST_TIMEOUT`: HTTP 请求超时，单位秒，默认 `10`
- `BILIBILI_LIVE_NOTIFY_STARTUP_CHECK_DELAY`: 启动后首次检查前的等待时间，单位秒，默认 `3`
- `BILIBILI_LIVE_NOTIFY_DATA_FILE`: 订阅数据存储文件，默认 `data/bilibili_live_notify/subscriptions.json`
- `BILIBILI_LIVE_NOTIFY_SOURCE`: 数据来源，支持 `proxy`、`api`、`auto`，默认 `proxy`
- `BILIBILI_LIVE_NOTIFY_PROXY_URL`: 代理服务地址模板，需包含 `{room_id}`，默认 `http://127.0.0.1:8000/bilibili/live?room_id={room_id}`
- `BILIBILI_LIVE_NOTIFY_API_BASE`: Bilibili 官方接口基础地址，仅 `api` 或 `auto` 回退时使用

## 代理服务协议

如果使用代理模式，插件期望 HTTP 接口返回如下结构：

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

仓库中的 [bilibili-proxy/main.py](/Users/hacchiroku/nonebot-plugin-bilibili-live-notify/bilibili-proxy/main.py) 就是兼容实现，插件默认按这个协议工作。

## 代理服务部署

最小启动方式：

```bash
uvicorn main:app --app-dir bilibili-proxy --host 0.0.0.0 --port 8000
```

如果代理和机器人不在同一台机器，把 `BILIBILI_LIVE_NOTIFY_PROXY_URL` 改成可访问地址即可。

## 指令

- `直播帮助`
- `订阅直播 <房间号> [备注]`
- `取消订阅直播 <房间号|备注>`
- `备注直播 <房间号|旧备注> <新备注>`
- `参与直播 <房间号|备注>`
- `取消参与直播 <房间号|备注>`
- `直播订阅列表`
- `我参与的直播`

## 测试

开发和发布前的本地验证说明见 [docs/development-testing.md](/Users/hacchiroku/nonebot-plugin-bilibili-live-notify/docs/development-testing.md)。

自动化测试执行：

```bash
pip install -e ".[test]"
pytest
```

## 发布到 PyPI

构建：

```bash
python -m build
```

上传：

```bash
python -m twine upload dist/*
```

## 自动发布

仓库已补充：

- GitHub CI: [ci.yml](/Users/hacchiroku/nonebot-plugin-bilibili-live-notify/.github/workflows/ci.yml)
- PyPI 发布工作流: [publish.yml](/Users/hacchiroku/nonebot-plugin-bilibili-live-notify/.github/workflows/publish.yml)

推荐流程：

1. 在 PyPI 后台把这个 GitHub 仓库配置为 Trusted Publisher
2. 在 GitHub 发一个 Release
3. `publish.yml` 自动构建并上传 PyPI

## 发布到 NoneBot 插件商店

建议顺序：

1. 先完成 PyPI 发布
2. 确认 README 已写清必要配置项和代理依赖
3. 再去 NoneBot 插件商店提交通知信息

这个项目属于“插件本体 + 外部代理服务”的结构，商店页面里最好明确写出：

- 需要配置 `BILIBILI_LIVE_NOTIFY_PROXY_URL`
- 默认推荐 `BILIBILI_LIVE_NOTIFY_SOURCE=proxy`
- 代理服务协议见本仓库 `bilibili-proxy/main.py`
- 可直接参考 [docs/nonebot-marketplace-submission.md](/Users/hacchiroku/nonebot-plugin-bilibili-live-notify/docs/nonebot-marketplace-submission.md)

## License

MIT
