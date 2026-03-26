# NoneBot 插件商店提交模板

以下内容是给 NoneBot 插件商店登记时使用的草稿，可以直接改后提交。

## 基础信息

- 插件名: `nonebot-plugin-bilibili-live-notify`
- 模块名: `nonebot_plugin_bilibili_live_notify`
- PyPI 名称: `nonebot-plugin-bilibili-live-notify`
- 适配器: `OneBot V11`
- 插件类型: `application`

## 简介

在 QQ 群中订阅 Bilibili 直播间，并在开播/下播时自动推送通知。支持群成员自行加入提醒名单，按参与者进行 `@` 提醒。

## 功能说明

- 群管理员订阅直播间
- 群成员参与或退出提醒
- 自动检测直播状态变化
- 开播/下播群消息通知
- 本地持久化订阅数据

## 使用前说明

本插件默认依赖一个 HTTP 代理服务来获取直播状态。

默认推荐配置：

```env
BILIBILI_LIVE_NOTIFY_SOURCE=proxy
BILIBILI_LIVE_NOTIFY_PROXY_URL=http://127.0.0.1:8000/bilibili/live?room_id={room_id}
```

代理服务协议和示例实现见仓库中的 `bilibili-proxy/main.py`。

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

## 仓库说明建议

如果商店页面允许填写额外说明，建议加上这段：

> 该插件默认通过自部署代理服务获取 Bilibili 直播状态。若未配置代理地址，安装后不会自动具备完整可用性。
