from __future__ import annotations

import asyncio
import json

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER

from .adapter_state import (
    dump_cookie,
    is_room_monitored,
    iter_web_live_bots,
    resolve_monitored_room_id,
    schedule_web_room_monitor,
)
from .runtime import export_path, managed_rooms, store

ADMIN_PERMISSION = SUPERUSER | GROUP_ADMIN | GROUP_OWNER


def get_group_rooms(group_id: int):
    return [
        (room_id, room)
        for room_id, room in store.subs.rooms.items()
        if group_id in room.groups
    ]


def match_rooms(group_rooms, keyword: str):
    if keyword.isdigit():
        room_id = int(keyword)
        canonical_room_id = resolve_monitored_room_id(room_id) or room_id
        return [(rid, room) for rid, room in group_rooms if rid == canonical_room_id]
    return [(rid, room) for rid, room in group_rooms if room.remark == keyword]


def build_choice_text(rooms):
    return "\n".join(
        f"{index}. {room.remark}（{room_id}）"
        for index, (room_id, room) in enumerate(rooms, 1)
    )


def build_adapter_config() -> list[dict[str, object]]:
    managed_room_ids = managed_rooms.list()
    web_bots = list(iter_web_live_bots())
    if not web_bots:
        return [
            {
                "cookie": "SESSDATA=请填入你的Cookie; bili_jct=请填入你的bili_jct;",
                "room_ids": managed_room_ids,
            }
        ]

    result: list[dict[str, object]] = []
    for index, bot in enumerate(web_bots):
        room_ids = sorted(
            {
                *[
                    int(getattr(room, "room_id"))
                    for room in getattr(bot, "rooms", {}).values()
                    if getattr(room, "room_id", None) is not None
                ],
                *(managed_room_ids if index == 0 else []),
            }
        )
        result.append(
            {
                "cookie": dump_cookie(bot.cookie),
                "room_ids": room_ids,
            }
        )
    return result


async def write_adapter_config() -> None:
    config_data = build_adapter_config()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config_data, ensure_ascii=False, indent=2)
    await asyncio.to_thread(export_path.write_text, payload, encoding="utf-8")


help_cmd = on_command(
    "直播帮助",
    aliases={"直播菜单", "直播指令"},
    priority=1,
    block=True,
)


@help_cmd.handle()
async def _handle_help():
    msg = Message()
    msg += MessageSegment.text(
        "这是直播订阅助手，可以自动推送直播开播 / 下播消息。\n"
        "\n【管理员】\n"
        "订阅直播 <房间号> [备注]\n"
        "取消订阅直播 <房间号|备注>\n"
        "备注直播 <房间号|旧备注> <新备注>\n"
        "直播监听列表\n"
        "更新直播监听配置\n"
        "导出直播监听配置\n"
        "\n【群成员】\n"
        "参与直播 <房间号|备注>\n"
        "取消参与直播 <房间号|备注>\n"
        "\n【查询】\n"
        "直播订阅列表\n"
        "我参与的直播"
    )
    await help_cmd.finish(msg)


sub_cmd = on_command(
    "订阅直播",
    permission=ADMIN_PERMISSION,
    priority=5,
    block=True,
)


@sub_cmd.handle()
async def _handle_subscribe(event: GroupMessageEvent):
    args = event.get_plaintext().strip().split(maxsplit=2)
    if len(args) < 2 or not args[1].isdigit():
        await sub_cmd.finish("用法：订阅直播 <房间号> [备注]")

    input_room_id = int(args[1])
    room_id = resolve_monitored_room_id(input_room_id) or input_room_id
    remark = args[2].strip() if len(args) >= 3 else str(room_id)

    await store.subscribe_group(
        room_id=room_id,
        remark=remark,
        group_id=event.group_id,
        creator_id=event.user_id,
    )

    reply = (
        f"已订阅直播 {room_id}\n"
        f"备注：{remark}\n"
        "该直播已加入本群监听，如需提醒请使用「参与直播」"
    )
    if not is_room_monitored(room_id):
        await managed_rooms.add(room_id)
        ok, message = schedule_web_room_monitor(room_id)
        await write_adapter_config()
        reply += (
            "\n该房间已加入待监听列表。"
            f"\n{message}"
            "\n插件已自动刷新导出配置文件。"
            f"\n文件：{export_path}"
            "\n若希望下次重启后继续生效，请将该文件内容同步到 BILIBILI_LIVE_BOTS"
        )
        if not ok:
            reply += "\n当前进程未能立即补挂监听，但导出配置已准备好"
    else:
        await managed_rooms.remove(room_id)
        await write_adapter_config()

    await sub_cmd.finish(reply)


unsub_cmd = on_command(
    "取消订阅直播",
    permission=ADMIN_PERMISSION,
    priority=5,
    block=True,
)


@unsub_cmd.handle()
async def _handle_unsubscribe(event: GroupMessageEvent):
    args = event.get_plaintext().strip().split(maxsplit=1)
    if len(args) < 2:
        await unsub_cmd.finish("用法：取消订阅直播 <房间号|备注>")

    matches = match_rooms(get_group_rooms(event.group_id), args[1])
    if not matches:
        await unsub_cmd.finish("未找到该直播")

    if len(matches) > 1:
        await unsub_cmd.finish("找到多个直播：\n" + build_choice_text(matches))

    room_id, room = matches[0]
    await store.unsubscribe_group(room_id, event.group_id)
    if store.get_room(room_id) is None and not is_room_monitored(room_id):
        await managed_rooms.remove(room_id)
    await write_adapter_config()
    await unsub_cmd.finish(f"已取消订阅 {room.remark}")


remark_cmd = on_command(
    "备注直播",
    permission=ADMIN_PERMISSION,
    priority=5,
    block=True,
)


@remark_cmd.handle()
async def _handle_remark(event: GroupMessageEvent):
    args = event.get_plaintext().strip().split(maxsplit=2)
    if len(args) < 3:
        await remark_cmd.finish("用法：备注直播 <房间号|旧备注> <新备注>")

    matches = match_rooms(get_group_rooms(event.group_id), args[1])
    if not matches:
        await remark_cmd.finish("未找到该直播")

    if len(matches) > 1:
        await remark_cmd.finish("找到多个直播：\n" + build_choice_text(matches))

    room_id, room = matches[0]
    old = room.remark
    await store.rename_room(room_id, args[2].strip())
    await remark_cmd.finish(f"已将备注从「{old}」修改为「{args[2].strip()}」")


join_cmd = on_command("参与直播", priority=5, block=True)


@join_cmd.handle()
async def _handle_join(event: GroupMessageEvent):
    args = event.get_plaintext().strip().split(maxsplit=1)
    if len(args) < 2:
        await join_cmd.finish("用法：参与直播 <房间号|备注>")

    matches = match_rooms(get_group_rooms(event.group_id), args[1])
    if not matches:
        await join_cmd.finish("本群未订阅该直播")

    if len(matches) > 1:
        await join_cmd.finish("找到多个直播：\n" + build_choice_text(matches))

    room_id, room = matches[0]
    await store.add_participant(room_id, event.group_id, event.user_id)
    await join_cmd.finish(f"你将收到 {room.remark} 的直播提醒")


leave_cmd = on_command("取消参与直播", priority=5, block=True)


@leave_cmd.handle()
async def _handle_leave(event: GroupMessageEvent):
    args = event.get_plaintext().strip().split(maxsplit=1)
    if len(args) < 2:
        await leave_cmd.finish("用法：取消参与直播 <房间号|备注>")

    matches = match_rooms(get_group_rooms(event.group_id), args[1])
    if not matches:
        await leave_cmd.finish("未找到该直播")

    if len(matches) > 1:
        await leave_cmd.finish("找到多个直播：\n" + build_choice_text(matches))

    room_id, room = matches[0]
    ok = await store.remove_participant(room_id, event.group_id, event.user_id)
    if not ok:
        await leave_cmd.finish("你未参与该直播")

    await leave_cmd.finish(f"已取消参与 {room.remark}")


list_cmd = on_command("直播订阅列表", priority=5, block=True)


@list_cmd.handle()
async def _handle_list(event: GroupMessageEvent):
    group_rooms = get_group_rooms(event.group_id)
    if not group_rooms:
        await list_cmd.finish("本群暂无直播订阅")

    text = "本群订阅的直播：\n"
    for room_id, room in group_rooms:
        count = len(room.groups[event.group_id].participants)
        text += f"- {room.remark}（{room_id}，{count} 人参与）\n"

    await list_cmd.finish(text.rstrip())


watch_list_cmd = on_command(
    "直播监听列表",
    permission=ADMIN_PERMISSION,
    priority=5,
    block=True,
)


@watch_list_cmd.handle()
async def _handle_watch_list():
    pending_rooms = [
        room_id for room_id in managed_rooms.list() if not is_room_monitored(room_id)
    ]
    if not pending_rooms:
        await watch_list_cmd.finish("当前没有待补充到 bilibili-live 适配器的房间")

    text = "待补充到 bilibili-live 适配器的房间：\n"
    for room_id in pending_rooms:
        room = store.get_room(room_id)
        name = room.remark if room is not None else str(room_id)
        text += f"- {name}（{room_id}）\n"
    await watch_list_cmd.finish(text.rstrip())


refresh_watch_cmd = on_command(
    "更新直播监听配置",
    permission=ADMIN_PERMISSION,
    priority=5,
    block=True,
)


@refresh_watch_cmd.handle()
async def _handle_refresh_watch():
    pending_rooms = [
        room_id for room_id in managed_rooms.list() if not is_room_monitored(room_id)
    ]
    if not pending_rooms:
        await refresh_watch_cmd.finish("当前没有需要补挂到 bilibili-live 适配器的房间")

    messages: list[str] = []
    failed = False
    for room_id in pending_rooms:
        ok, message = schedule_web_room_monitor(room_id)
        failed = failed or not ok
        messages.append(f"- {message}")

    suffix = (
        "\n当前是运行时补挂，若希望下次重启后继续生效，"
        "仍需执行「导出直播监听配置」并更新 BILIBILI_LIVE_BOTS"
    )
    if failed:
        suffix = (
            "\n部分房间未能自动补挂。"
            "\n你仍可执行「导出直播监听配置」后重启机器人生效"
        )
    await refresh_watch_cmd.finish("监听补挂结果：\n" + "\n".join(messages) + suffix)


export_cmd = on_command(
    "导出直播监听配置",
    permission=ADMIN_PERMISSION,
    priority=5,
    block=True,
)


@export_cmd.handle()
async def _handle_export():
    await write_adapter_config()
    await export_cmd.finish(
        "已导出适配器配置。\n"
        f"文件：{export_path}\n"
        "请将该文件内容复制到 BILIBILI_LIVE_BOTS，并重启机器人生效"
    )


mine_cmd = on_command("我参与的直播", priority=5, block=True)


@mine_cmd.handle()
async def _handle_mine(event: GroupMessageEvent):
    result = []
    for _, room in get_group_rooms(event.group_id):
        if event.user_id in room.groups[event.group_id].participants:
            result.append(room)

    if not result:
        await mine_cmd.finish("你当前没有参与任何直播")

    text = "你参与的直播：\n"
    for room in result:
        text += f"- {room.remark}\n"

    await mine_cmd.finish(text.rstrip())
