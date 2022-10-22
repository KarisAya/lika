from pathlib import Path
from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    MessageSegment
    )
import os

import jieba
import jieba.posseg as pseg

jieba.load_userdict(str(Path(os.path.join(os.path.dirname(__file__),'用户词典.txt'))))

def analys_text(msg:str) -> list:
    """
    分析句子
    """
    event_list = []
    i = 0
    for seg, flag in pseg.cut(msg, use_paddle = True):
        if seg == "你":
            event_list.append(["name",seg, 1])
        elif seg in ["我","咱"]:
            event_list.append(["name",seg, 2])
        elif flag == "c":
            event_list.append(["replay",seg])
        elif flag == "l":
            if seg == "我爱你":
                event_list.insert(i,['event',"love"])
                event_list.append(["done",seg])
            elif "好" in seg:
                event_list.insert(i,['event',"hello"])
                event_list.append(["hello",seg])
            else:
                event_list.append(["other",seg,flag])
        elif flag == "v":
            if seg == "喜欢":
                event_list.append(["like",seg])
            elif seg == "爱":
                event_list.append(["love",seg])
            elif seg == "叫":
                event_list.append(["call",seg])
            elif seg == "是":
                event_list.append(["is",seg])
            elif seg in ["加入","加群","进群"]:
                event_list.insert(i,['event',"join"])
                event_list.append(["done",seg])
            else:
                event_list.append(["do",seg])
        elif flag == "f":
            event_list.append(["ignore",seg])
        elif flag == "nset":
            event_list.append(["nset",seg])
        elif flag == "n":
            if seg == "名字":
                event_list.append(["info",seg])
            else:
                event_list.append(["n",seg])
        elif flag == "r":
            if "什么" in seg or "啥" in seg:
                event_list.append(["what",seg])
            elif seg == "谁":
                event_list.append(["who",seg])
            elif seg == "怎么样":
                event_list.append(["ignore",seg,flag])
            else:
                event_list.append(["other",seg,flag])
        elif flag == "x":
            event_list.insert(i,['event',"cut"])
            event_list.append(["done",seg])
        elif flag == "y":
            if seg in ["吗","嘛"]:
                event_list.insert(i,['event',"ask"])
                event_list.append(["done",seg])
            else:
                event_list.append(["y",seg])
        elif flag in ["z","w"]:
            event_list.append(["other",seg,flag])
        elif flag in ["d","uj","ul"]:
            if seg == "不":
                event_list.append(["not",seg])
            else:
                event_list.append(["ignore",seg])
        else:
            event_list.append(["other",seg,flag])
        i += 1
    else:
        return event_list

def analys_list(event_list:list) -> list:
    """
    分析事件列表
    """
    N = len(event_list)
    i = 0
    new_list = []
    event = []
    flag = 0
    while i < N:
        seg = event_list[i]
        new_list.append(seg)
        i += 1
        if seg[0] in ["not","do","call","is","like","love","name","what","who"]:
            event.append(seg)
            continue
        if seg[0] in ["ignore", "y", "info"]:
            continue
        if len(event) > 1:
            new_list.insert(i-1, sub_analys_list(event))
        event = []
    else:
        if len(event) > 1:
            new_list.insert(i, sub_analys_list(event))

    return new_list

def sub_analys_list(event_list:list) -> list:
    """
    分析主事件
    """
    A = 0
    B = 0
    do = ""
    ask = None
    for seg in event_list:
        if not A and not do and seg[0] == "name":
            A = seg[2]
            seg[0] = "done"
        elif not do and seg[0] == "not":
            do = "not"
            seg[0] = "done"
        elif seg[0] in ["do","call","is","like","love"]:
            if do == "not":
                do = f"not_{seg[0]}"
                seg[0] = "done"
            else:
                if not do or do in ["do","call","is","like","love"]:
                    do = seg[0]
                    seg[0] = "done"
                else:
                    pass
        elif do and seg[0] == "name":
            seg[0] = "done"
            if A == seg[2]:
                continue
            elif A == 0:
                A = 1 if seg[2] == 2 else 2

            B = seg[2]

        if seg[0] in ["what","who"]:
            ask = seg[0]
            seg[0] = "done"

    if A and do == "call":
        if ask:
            if B:
                if B == 1:
                    return ['event',"ask_selfname"]
                elif B == 2:
                    return ['event',"ask_customername"]
            else:
                if A == 1:
                    return ['event',"ask_selfname"]
                elif A == 2:
                    return ['event',"ask_customername"]
        else:
            if B:
                if B == 1:
                    return ['event',"set_selfname"]
                elif B == 2:
                    return ['event',"set_customername"]
            else:
                if A == 1:
                    return ['event',"set_selfname"]
                elif A == 2:
                    return ['event',"hello"]
    elif do == "is":
        if ask:
            if A == 1:
                return ['event',"whatis_self"]
            elif A == 2:
                if ask == "who":
                    return ['event',"ask_customername"]
                else:
                    return ['event',"whatis_customer"]
            else:
                return ['event',"whatis_other"]
        else:
            if A == 1:
                return ['event',"set_selfis"]
            elif A == 2:
                return ['event',"set_customeris"]
    elif do == "like":
        if B == 1:
            return ['event',"like"]
        elif B == 2:
            return ['event',"wait_like"]
        elif A == 2:
            return ['event',"set_customerlike"]
        else:
            return ['event',"unknow"]
    elif do == "love":
        if B == 1:
            return ['event',"love"]
        elif B == 2:
            return ['event',"wait_love"]
        elif A == 2:
            return ['event',"set_customerlove"]
        else:
            return ['event',"unknow"]
    elif "not" in do:
        if do == "not_like":
            if ask and not B:
                if A == 1:
                    return ['event',"ask_selflike"]
                elif A == 2:
                    return ['event',"ask_customerlike"]
            else:
                if B == 1:
                    return ['event',"not_like"]
                elif B == 2:
                    return ['event',"wait_like_re"]
                elif A == 1:
                    return ['event',"ask_like"]
                elif A == 2:
                    return ['event',"set_customernotlike"]
                else:
                    return ['event',"not_like_do"]
        elif do == "not_love":
            if ask and not B:
                if A == 1:
                    return ['event',"ask_selflove"]
                elif A == 2:
                    return ['event',"ask_customerlove"]
            else:
                if B == 1:
                    return ['event',"not_love"]
                elif A == 1 and B == 2:
                    return ['event',"wait_love_re"]
                elif A == 1:
                    return ['event',"ask_love"]
                elif A == 2:
                    return ['event',"set_customernotlove"]
                else:
                    return ['event',"not_like_do"]
        else:
            return ['event',do]
    else:
        return ['event',"unknow"]

def analys_event(event_list:list) -> dict:
    """
    组合事件
    """
    analys = {
        "tag":"",
        "param":{}
        }
    tag = []
    for seg in event_list:
        if seg[0] == "event" and seg[0] != "cut":
            if seg[0] == "cut":
                continue
            else:
                tag.append(seg[1])
                flag = 0
        elif seg[0] == "done":
            continue
        else:
            if not tag:
                analys["param"].setdefault("before",[]).append(seg)
            else:
                if flag == 0:
                    if not analys["param"].get(tag[-1]):
                        analys["param"].setdefault(tag[-1],[]).append(seg)
                        flag = 1
                    else:
                        analys["param"].setdefault(tag[-1] + "_extra",[]).append(seg)
                        flag = 2
                elif flag == 1:
                    analys["param"][tag[-1]].append(seg)
                elif flag == 2:
                    analys["param"][tag[-1] + "_extra"].append(seg)

    else:
        if len(tag) == 1:
            analys["tag"] = tag[0]
        elif len(tag) > 1:
            if "wait_love" in tag:
                analys["tag"] = "wait_love"
            elif "wait_like" in tag:
                analys["tag"] = "wait_like"
            elif "wait_like_re" in tag:
                analys["tag"] = "wait_like_re"
            elif "wait_love_re" in tag:
                analys["tag"] = "wait_love_re"
            elif "ask" in tag:
                if "set_selfis" in tag:
                    analys["tag"] = "ask_self"
                elif "join" in tag:
                    analys["tag"] = "ask_join"
                elif "ask_love" in tag:
                    analys["tag"] = "ask_love"
                elif "ask_like" in tag:
                    analys["tag"] = "ask_like"
                else:
                    analys["tag"] = tag
            else:
                analys["tag"] = tag[0]
        else:
            pass
    return analys

def analys(msg:str) -> dict:
    if (not msg) or msg.isspace():
        return {"tag":"hello","param":[]}
    return analys_event(analys_list(analys_text(msg)))

def param(data: dict, key: str, ignore: set = set()) -> str:
    """
    参数拼接
    """
    tag = alive_seg(data["param"].get(key,[]),ignore)
    if len(tag) == 1:
        return tag[0][1]
    else:
        msg = ""
        for i in tag:
            msg += i[1]
        else:
            return msg

def alive_seg(seg_list:list ,ignore: set = set()) -> dict:
    """
    未处理seg_list
    """
    ignore = {"done"} | ignore
    tag = []
    for seg in seg_list:
        if seg[0] in ignore:
            continue
        else:
            tag.append(seg)
    return tag