from pathlib import Path

import os
import random

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .data_source import Bot_NICKNAME

path = os.path.join(os.path.dirname(__file__), "resource")

# 载入个人词库

MyThesaurus = {}

Thesaurus_list = set(os.listdir(Path(path))) - {"leaf.json", "data.json"}

for file in Thesaurus_list:
    try:
        with open(Path(path) / file, "r", encoding="utf8") as f:
            Thesaurus = json.load(f)
        logger.info(f"{i} 加载成功~")
    except UnicodeDecodeError:
        logger.info(f"{i} utf8解码出错！！！")
        continue
    except Exception as error:
        logger.info(f"错误：{error} {i} 加载失败...")
        continue
    for key in Thesaurus.keys():
        if not key in MyThesaurus.keys():
            MyThesaurus.update({key:[]})
        if type(Thesaurus[key]) == list:
            MyThesaurus[key] += Thesaurus[key]
        else:
            logger.info(f"\t文件 {i} 内 {key} 词条格式错误。")

# 载入首选词库

with open(Path(path) / "leaf.json", "r", encoding="utf8") as f:
    LeafThesaurus = json.load(f)

# 载入词库(这个词库有点涩)

with open(Path(path) / "data.json", "r", encoding="utf8") as f:
    AnimeThesaurus = json.load(f)

unknow_reply = [
    f"{Bot_NICKNAME}不懂...",
    "呜喵？",
    "没有听懂喵...",
    "装傻（",
    "呜......",
    "喵喵？",
    "(,,• ₃ •,,)",
    "没有理解呢...",
]

def get_chat_result(resource:dict, text: str) -> str:
    """
    从 resource 中获取回应
    """
    if len(text) < 21:
        keys = resource.keys()
        for key in keys:
            if text.find(key) != -1:
                return random.choice(resource[key])