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
import re

import jieba
import jieba.posseg as pseg

jieba.load_userdict(str(Path(os.path.join(os.path.dirname(__file__),'用户词典.txt'))))

do_set = {"call","is","like","love"}

def analys_text(msg:str) -> list:
    """
    分析句子
    """
    event_list = [["event","start"]]
    i = 1
    for seg, flag in pseg.cut(msg, use_paddle = True):
        if seg == "你":
            event_list.append(["name",seg, 1])
        elif seg in ["我","咱"]:
            event_list.append(["name",seg, 2])
        elif flag == "c":
            event_list.append(["replay",seg])
        elif flag == "l":
            if seg == "我爱你":
                event_list.insert(i,["event","love"])
                event_list.append(["done",seg])
            elif "好" in seg:
                event_list.insert(i,["event","hello"])
                event_list.append(["hello",seg])
            else:
                event_list.append(["other",seg,flag])
        elif flag == "v":
            if seg == "喜欢":
                event_list.append(["like",seg])
            elif seg == "讨厌":
                event_list.append(["not",""])
                event_list.append(["like",seg])
            elif seg == "爱":
                event_list.append(["love",seg])
            elif seg == "叫":
                event_list.append(["call",seg])
            elif seg == "是":
                event_list.append(["is",seg])
                event_list.append(["name","",0])
            elif seg == "不想":
                event_list.append(["not",seg])
            else:
                event_list.append(["do",seg])
        elif flag == "f":
            event_list.append(["ignore",seg])
        elif flag == "nset":
            event_list.append(["nset",seg])
        elif flag == "n":
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
            event_list.insert(i,["event","cut"])
            event_list.append(["done",seg])
        elif flag == "y":
            if seg in ["吗","嘛"]:
                event_list.insert(i,["event","ask"])
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
    j = 1
    new_list = []
    event = []
    flag = 0
    while i < N:
        seg = event_list[i]
        new_list.append(seg)
        i += 1
        if seg[0] in {"name","what","who","not","do"} | do_set:
            event.append(seg)
        elif seg[0] in {"ignore", "y"}:
            j += 1
            continue
        else:
            if len(event) > 1:
                new_list.insert(i-j, event_tag(event))
            event = []
        j = 1
    else:
        if len(event) > 1:
            new_list.insert(i, event_tag(event))

    return new_list

def A_B_do_ask(event_list:list):
    """
    生成：A_B_do_ask
    """
    A = 0
    B = 0
    do = ""
    ask = ""
    for seg in event_list:
        if seg[0] in {"what","who"}:
            ask = seg[0]
            seg[0] = "done"
        if not A and not do and seg[0] == "name":
            A = seg[2]
            seg[0] = "done"
        elif not do and seg[0] == "not":
            do = "not"
            seg[0] = "done"
        elif seg[0] in {"do"} | do_set:
            if not do:
                do = seg[0] if seg[0] != "do" else ("do_" + seg[1])
                seg[0] = "done"
                tmp = seg
            if do == "not":
                do = "not_" + seg[0] if seg[0] != "do" else ("do_" + seg[1])
                seg[0] = "done"
            elif do[:2] == "do":
                tmp[0] = "event"
                tmp[1] = "wait"
                do = seg[0] if seg[0] != "do" else ("do_" + seg[1])
                seg[0] = "done"
            else:
                pass
        elif do and seg[0] == "name":
            B = seg[2]
            seg[0] = "done"
    else:
        pass

    return A, B, do, ask
def event_tag(event_list:list) -> list:
    """
    生成：event_tag
    """
    A, B, do, ask = A_B_do_ask(event_list)
    if do == "call":
        if ask:
            if B == 1:
                return ["event","ask_selfname"]
            elif B == 2:
                return ["event","ask_customername"]
            elif A == 1:
                return ["event","ask_selfname"]
            elif A == 2:
                return ["event","ask_customername"]
            else:
                return ["event","whatis_other"]
        else:
            if B == 1:
                return ["event","set_selfname"]
            elif B == 2:
                return ["event","set_customername"]
            elif A == 1:
                return ["event","set_selfname"]
            elif A == 2:
                return ["event","set_customername"]
            else:
                return ["event","set_otheris"]
    elif do == "is":
        if ask == "who":
            if A == 1:
                return ["event","ask_selfname"]
            elif A == 2:
                return ["event","ask_customername"]
            else:
                return ["event","question",f"NAME{A}"]
        elif ask == "what":
            return ["event","question",f"NAME{A}"]
        else:
            return ["event","learn",f"NAME{A}",f"NAME{B}"]
    elif do == "like":
        if not ask and B == 1:
            return ["event","like"]
        elif B == 2:
            return ["event","wait_like"]
        elif A == 1:
            if ask == "what":
                return ["event","ask_like_what"]
            elif ask == "who":
                return ["event","ask_like_who"]
        elif A == 2:
            return ["event","set_customerlike"]
        else:
            return ["event","like_do"]
    elif do == "love":
        if not ask and B == 1:
            return ["event","love"]
        elif B == 2:
            return ["event","wait_love"]
        elif A == 1:
            if ask == "what":
                return ["event","ask_love_what"]
            elif ask == "who":
                return ["event","ask_love_who"]
        elif A == 2:
            return ["event","set_customerlove"]
        else:
            return ["event","love_do"]
    elif "not_" in do:
        if do == "not_like":
            if not ask and B == 1:
                return ["event","not_like"]
            elif B == 2:
                return ["event","wait_like_re"]
            elif A == 1:
                if ask == "what":
                    return ["event","ask_like_what"]
                elif ask == "who":
                    return ["event","ask_like_who"]
            elif A == 2:
                return ["event","set_customernotlike"]
            else:
                return ["event","not_like_do"]
        elif do == "not_love":
            if not ask and B == 1:
                return ["event","not_love"]
            elif B == 2:
                return ["event","wait_love_re"]
            elif A == 1:
                if ask == "what":
                    return ["event","ask_love_what"]
                elif ask == "who":
                    return ["event","ask_love_who"]
            elif A == 2:
                return ["event","set_customernotlove"]
            else:
                return ["event","not_love_do"]
    else:
        return["event",f"{A} {B} {do} {ask if ask else 'None'}"]

def analys_event(event_list:list) -> dict:
    """
    组合事件
    """
    analys = {
        "tag":"",
        "param":{},
        }
    tag = []
    for seg in event_list:
        if seg[0] == "event":
            if seg[1] == "cut":
                flag = 0
                continue
            else:
                tag.append(seg[1])
                key = tag[-1]
                if not analys["param"].setdefault(key,[]):
                    if len(tag) > 1:
                        analys["param"][key].append(["before",tag[-2]])
                        if key == "learn":
                            analys["param"][tag[-2]].insert(0,["info",seg[2]])
                            analys["param"][key].append(["info",seg[3]])
                        elif key == "question":
                            analys["param"][key].append(["info",seg[2]])
                    flag = 1
                else:
                    flag = 0
        elif seg[0] == "done":
            continue
        else:
            key = tag[-1]
            if flag == 0:
                if not analys["param"].get(key):
                    analys["param"].setdefault(key,[])
                    if len(tag) > 1:
                        analys["param"][key].append(["before",tag[-2]])
                    analys["param"][key].append(seg)
                    flag = 1
                else:
                    analys["param"].setdefault(key + "_extra",[])
                    if len(tag) > 1:
                        analys["param"][key + "_extra"].append(["before",tag[-2]])
                    analys["param"][key + "_extra"].append(seg)
                    flag = 2
            elif flag == 1:
                analys["param"][key].append(seg)
            elif flag == 2:
                analys["param"][key + "_extra"].append(seg)

    else:
        tag = tag[1:]
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
                elif "ask_love" in tag:
                    analys["tag"] = "ask_love"
                elif "ask_like" in tag:
                    analys["tag"] = "ask_like"
                else:
                    analys["tag"] = tag_format(tag)
            elif "wait" in tag:
                if "love" in tag:
                    analys["tag"] = "wait_love"
                elif "like" in tag:
                    analys["tag"] = "wait_like"
                else:
                    analys["tag"] = tag_format(tag)
            else:
                analys["tag"] = tag_format(tag)
        else:
            pass
    return analys

def tag_format(tag:list) -> str:
    output = set(tag) - {"ask","wait"}
    if output:
        return list(output)[0]
    else:
        return None

def analys(msg:str) -> dict:
    if (not msg) or msg.isspace():
        return {"tag":"hello","param":[]}
    return analys_event(analys_list(analys_text(msg)))

def analys_param(data: dict, key: str, ignore: set = set()):
    """
    分析参数
    """
    tag = None
    before = None
    tag = data["param"].get(key)
    if tag:
        tag, before = analys_seg(tag,ignore)
        if before:
            before = data["param"].get(before)
            if before:
                before = analys_seg(before,ignore)

    return tag, before

def analys_seg(seg_list:list ,ignore: set = set()) -> dict:
    """
    分析片段。
    """
    ignore = {"done"} | ignore
    tag = []
    before = None
    for seg in seg_list:
        if seg[0] in ignore:
            continue
        elif seg[0] == "before":
            before = seg[1]
        else:
            tag.append(seg)
    return tag, before