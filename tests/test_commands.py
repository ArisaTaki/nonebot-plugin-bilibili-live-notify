from __future__ import annotations

import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter, Bot, GroupMessageEvent, Message
from nonebug import App


def make_group_event(message: str, *, user_id: int, group_id: int) -> GroupMessageEvent:
    return GroupMessageEvent(
        time=1,
        self_id=123456,
        post_type="message",
        sub_type="normal",
        user_id=user_id,
        message_type="group",
        message_id=1,
        message=Message(message),
        original_message=Message(message),
        raw_message=message,
        font=0,
        sender={"user_id": user_id, "nickname": "tester", "card": "", "role": "admin"},
        group_id=group_id,
    )


@pytest.mark.asyncio
async def test_subscribe_and_list(app: App):
    from nonebot_plugin_bilibili_live_notify.commands import list_cmd, sub_cmd

    async with app.test_matcher(sub_cmd) as ctx:
        bot = ctx.create_bot(
            base=Bot,
            adapter=nonebot.get_adapter(Adapter),
            self_id="123456",
        )
        event = make_group_event("订阅直播 12345 测试主播", user_id=123456, group_id=10000)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "已订阅直播 12345\n备注：测试主播\n该直播已加入本群监听，如需提醒请使用「参与直播」",
            result=None,
            bot=bot,
        )
        ctx.should_finished()

    async with app.test_matcher(list_cmd) as ctx:
        bot = ctx.create_bot(
            base=Bot,
            adapter=nonebot.get_adapter(Adapter),
            self_id="123456",
        )
        event = make_group_event("直播订阅列表", user_id=10001, group_id=10000)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "本群订阅的直播：\n- 测试主播（12345，0 人参与）",
            result=None,
            bot=bot,
        )
        ctx.should_finished()
