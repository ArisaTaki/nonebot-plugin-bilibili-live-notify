# NoneBot 插件商店提交文案

以下内容可直接作为插件商店提交时的填写参考。

## 插件名

`nonebot-plugin-bilibili-live-notify`

## 模块名

`nonebot_plugin_bilibili_live_notify`

## 适配器

`OneBot V11`

## 简介

在 QQ 群中订阅 Bilibili 直播间，并在开播 / 下播时自动推送通知。支持群成员自行加入提醒名单，并对参与成员进行 `@` 提醒。

## 功能说明

- 群管理员订阅直播间
- 群成员参与或退出提醒
- 开播 / 下播自动推送
- 本地持久化订阅状态
- 支持代理服务获取直播状态

## 使用前说明

本插件默认依赖一个可访问的直播状态代理服务。

推荐最小配置：

```env
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
```

仓库内提供了兼容的 FastAPI 代理实现：`bilibili-proxy/main.py`。

## 常用指令

- `订阅直播 <房间号> [备注]`
- `取消订阅直播 <房间号|备注>`
- `备注直播 <房间号|旧备注> <新备注>`
- `参与直播 <房间号|备注>`
- `取消参与直播 <房间号|备注>`
- `直播订阅列表`
- `我参与的直播`

## 必要配置项

- `BILIBILI_LIVE_NOTIFY_SOURCE`
- `BILIBILI_LIVE_NOTIFY_PROXY_URL`
