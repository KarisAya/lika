from nonebot.plugin.on import on_command, on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment

from pathlib import Path

import re
import random
import time
import asyncio

from nonebot import logger

from .data_source import lika, Bot_NICKNAME
from .kawaii_robot import MyThesaurus, LeafThesaurus, AnimeThesaurus, get_chat_result, unknow_reply

async def hello(event: MessageEvent) -> bool:
    customer = lika.customer_data.get(str(event.user_id))
    if customer and customer["nickname"]:
        flag = event.message.extract_plain_text().startswith(customer["nickname"])
    else:
        flag = False
    return flag or event.is_tome()

talk = on_message(rule = hello, priority = 99)

@talk.handle()
async def _(event: MessageEvent):
    msg, nickname = lika.text(event)

    # 从 lika 中获取结果
    if result := lika.lika(event):
        if isinstance(result,list):
            for x in result:
                await talk.send(x)
                await asyncio.sleep(1)
            else:
                await talk.finish()
        else:
            await talk.finish(result)

    # 从个人字典里获取结果
    if result := get_chat_result(MyThesaurus, msg):
        await talk.finish(Message(result))

    # 从 LeafThesaurus 里获取结果
    if result := get_chat_result(LeafThesaurus,msg):
        await talk.finish(Message(result.replace("name", nickname)))

    # 从 AnimeThesaurus 里获取结果
    if result := get_chat_result(AnimeThesaurus,msg):
        await talk.finish(Message(result.replace("你", nickname)))
    
    # 不明白的内容

    with open('note.txt','w+',encoding='utf8')as f:
        f.write(msg)

    await talk.finish(Message(random.choice(unknow_reply)))
