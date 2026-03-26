from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER

from .runtime import store

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
        return [(rid, room) for rid, room in group_rooms if rid == room_id]
    return [(rid, room) for rid, room in group_rooms if room.remark == keyword]


def build_choice_text(rooms):
    return "\n".join(
        f"{index}. {room.remark}（{room_id}）"
        for index, (room_id, room) in enumerate(rooms, 1)
    )


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

    room_id = int(args[1])
    remark = args[2].strip() if len(args) >= 3 else str(room_id)

    store.subscribe_group(
        room_id=room_id,
        remark=remark,
        group_id=event.group_id,
        creator_id=event.user_id,
    )

    await sub_cmd.finish(
        f"已订阅直播 {room_id}\n"
        f"备注：{remark}\n"
        "该直播已加入本群监听，如需提醒请使用「参与直播」"
    )


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
    store.unsubscribe_group(room_id, event.group_id)
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
    store.rename_room(room_id, args[2].strip())
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
    store.add_participant(room_id, event.group_id, event.user_id)
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
    ok = store.remove_participant(room_id, event.group_id, event.user_id)
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
