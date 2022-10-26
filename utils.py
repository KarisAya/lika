from pathlib import Path
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
    for seg, flag in pseg.cut(msg, use_paddle = True):
        if seg == "你":
            event_list.append(["name",seg, 1])
        elif seg in ["我","咱"]:
            event_list.append(["name",seg, 2])
        elif flag == "c":
            event_list.append(["replay",seg])
        elif flag == "l":
            if seg == "我爱你":
                event_list.append(["event","love"])
                event_list.append(["done",seg])
            elif "好" in seg:
                event_list.append(["event","hello"])
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
            event_list.append(["event","cut"])
            event_list.append(["done",seg])
        elif flag == "y":
            if seg in ["吗","嘛"]:
                event_list.append(["event","ask"])
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
    else:
        return event_list

def analys_list(event_list:list) -> list:
    """
    分析事件列表
    """
    new_list = []
    event = []
    for seg in event_list:
        if seg[0] in {"name","what","who","not"}:
            event.append(seg)
        elif seg[0] in {"do"} | do_set:
            event.append(seg)
        elif seg[0] in {"ignore", "y"}:
            pass
        else:
            if len(event) > 1:
                new_list.append(event_tag(event))
            event = []
        new_list.append(seg)
    else:
        if len(event) > 1:
            new_list.append(event_tag(event))
            
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
            elif do == "not":
                do = "not_" + seg[0] if seg[0] != "do" else ("do_" + seg[1])
                seg[0] = "done"
            elif do.startswith("do_"):
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
    elif do.startswith("not_"):
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
            key = seg[1]
            if key in analys["param"]:
                extra = 0
                tmp = key
                while tmp in analys["param"]:
                    tmp = key + f"_extra_{extra}"
                    extra += 1
                else:
                    key = tmp
            tag.append(key)
            analys["param"][key] = []
            if len(tag) > 1:
                analys["param"][key].append(["before",tag[-2]])
                if key.startswith("learn"):
                    analys["param"][tag[-2]].insert(0,["info",seg[2]])
                    analys["param"][key].append(["info",seg[3]])
                elif key.startswith("question"):
                    analys["param"][key].append(["info",seg[2]])
        else:
            if seg[0] == "done":
                continue
            else:
                analys["param"][tag[-1]].append(seg)
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
                    analys["tag"] = tag_format(tag)[0]
            elif "wait" in tag:
                if "love" in tag:
                    analys["tag"] = "wait_love"
                elif "like" in tag:
                    analys["tag"] = "wait_like"
                else:
                    analys["tag"] = tag_format(tag)[0]
            else:
                analys["tag"] = tag_format(tag)[0]
        else:
            pass
    return analys

def tag_format(tag:list) -> list:
    output = []
    for x in tag:
        if x in ["start","cut","ask","wait"] or x.startswith("cut"):
            pass
        else:
            output.append(x)
    return output



def analys(msg:str) -> dict:
    if (not msg) or msg.isspace():
        return {"tag":"hello","param":[]}
    return analys_event(analys_list(analys_text(msg)))

def analys_seg(seg_list:list ,ignore: set = set()) -> dict:
    """
    分析片段。
    """
    ignore = {"done"} | ignore
    tag = ""
    before = None
    for seg in seg_list:
        if seg[0] in ignore:
            continue
        elif seg[1] == "NAME0":
            continue
        elif seg[0] == "before":
            before = seg[1]
        else:
            tag += seg[1]
    return tag, before