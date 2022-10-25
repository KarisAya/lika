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
from nonebot.log import logger

import nonebot
import random
import time

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .config import Config

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config.dict())

Bot_NICKNAME = list(global_config.nickname)[0] 
data_path = config.data_path

from .text import asdict
from .utils import analys, param


action_event = [
    "hello",
    ]


class Manager:
    def __init__(self):
        self.file = Path(data_path / "data" / "lika" )
        if self.file.exists():
            pass
        else:
            self.file.mkdir(parents=True, exist_ok=True)

        self.customer_data_file = Path(data_path / "data" / "lika" / "customer_data.json")
        if self.customer_data_file.exists():
            with open(self.customer_data_file, "r", encoding="utf8") as f:
                self.customer_data = json.load(f)
        else:
            self.customer_data = {}

        self.group_data_file = Path(data_path / "data" / "lika" / "group_data.json")
        if self.group_data_file.exists():
            with open(self.group_data_file, "r", encoding="utf8") as f:
                self.group_data = json.load(f)
        else:
            self.group_data = {}

        self.replay_file = Path(data_path / "data" / "lika" / "replay_data.json")
        if self.replay_file.exists():
            with open(self.file, "r", encoding="utf8") as f:
                self.replay_data = json.load(f)
        else:
            self.replay_data = asdict

    class save():
        def customer_data():
            with open(lika.customer_data_file, "w", encoding="utf8") as f:
                json.dump(lika.customer_data, f, ensure_ascii = False, indent = 4)
        def group_data():
            with open(lika.group_data_file, "w", encoding="utf8") as f:
                json.dump(lika.group_data, f, ensure_ascii = False, indent = 4)

    def text(self, event: MessageEvent) -> str:
        """
        处理event:
        """
        customer = self.customer_data.get(str(event.user_id))
        if customer:
            NAME1 = customer["nickname"]
            NAME2 = self.nickname(customer)
        else:
            NAME1 = None
            NAME2 = event.sender.nickname or event.sender.card

        for segment in event.message:
            if segment.type == "text":
                segment.data["text"] = segment.data["text"][len(NAME1):] if NAME1 and segment.data["text"].startswith(NAME1) else segment.data["text"]
                return segment.data["text"], NAME2
        else:
            return None, NAME2

    def sign(self, event: MessageEvent) -> bool:
        """
        领养
        :param event: MessageEvent
        """
        user_id = str(event.user_id)
        if self.customer_data.get(user_id):
            self.customer_data[user_id]["customer"]["sex"] = event.sender.sex
            self.customer_data[user_id]["customer"]["name"] = event.sender.nickname or event.sender.card
            return False
        else:
            self.customer_data[user_id] = {
                "customer":{
                    "id":event.user_id,
                    "sex":event.sender.sex,
                    "name":event.sender.nickname or event.sender.card,
                    "nickname":"",
                    "title":"",
                    },
                "nickname":"",
                "title":"",
                "countdown":0,
                "cd":time.time(),
                "lika":0,
                "love":50,
                "happy":50,
                "todo":"nothing",
                "do":"nothing",
                "done":[],
                "memory":{}
                }
            self.save.customer_data()
            return True

    def action(self, customer: dict, data: dict):
        """
        行动的前置处理
        """
        if customer["love"] > 100:
            customer["love"] = 100
        elif customer["love"] < 0:
            customer["love"] = 0

        if customer["happy"] > 100:
            customer["happy"] = 100
        elif customer["happy"] < 0:
            customer["happy"] = 0

        if customer["todo"] == data["tag"]:
            if time.time() > customer["cd"] + 30:
                customer["countdown"] -= 1
                customer["cd"] = time.time()
        else:
            customer["countdown"] -= 1
            customer["do"] = customer["todo"]
            customer["todo"] = data["tag"]
            customer["done"].append(data["tag"])
            while len(customer["done"]) > 5:
                del customer["done"][0]

        if customer["countdown"] < 1:
            customer["lika"] += random.randint(0,5)
            customer["countdown"] = random.randint(0,10)

    def nickname(self, customer: dict) -> str:
        """
        返回客人的名字
        """
        if customer["customer"]["nickname"]:
            return customer["customer"]["nickname"]
        else:
            if len(customer["customer"]["name"]) <= 7:
                return customer["customer"]["name"]
            else:
                return customer["customer"]["name"][:2] + random.choice(["酱","亲","ちゃん","桑"])

    def replay(self, customer: dict, replay_data:dict, emoji: bool = True) -> str:
        """
        回复内容
        """
        if customer["happy"] <= 25:
            happy = "失落"
        elif 25 < customer["happy"] <= 50:
            happy = "平淡"
        elif 50 < customer["happy"] <= 75:
            happy = "开心"
        else:
            happy = "超开心"

        msg = random.choice(replay_data[happy])

        if msg[0] == " ":
            msg = msg[1:]
        else:
            if emoji and random.randint(0,300) < 50 + customer["happy"]:
                msg += random.choice(self.replay_data["status"][happy])

        NAME1 = customer["nickname"] or Bot_NICKNAME
        NAME2 = self.nickname(customer)
        return msg.replace("NAME1", NAME1).replace("NAME2", NAME2)

    def lika(self, event: MessageEvent):
        """
        事件处理中心
        """
        data = analys(event.message.extract_plain_text())
        flag = self.sign(event)
        customer = self.customer_data[str(event.user_id)]
        if flag:
            tag = data["tag"]
            if tag == "hello":
                pt = random.randint(1,3)
                customer["love"] += pt
                return f'你好！初次见面！（好感度+{pt}）'
            elif tag == "like":
                pt0 = random.randint(1,5)
                customer["love"] += pt0
                pt1 = random.randint(1,5)
                customer["happy"] += pt1
                return f'诶嘿~({Bot_NICKNAME}卖了个萌，好感度+{pt0}，心情+{pt1}）'
            elif tag == "love":
                pt = random.randint(5,10)
                customer["love"] += pt
                return f'呜哇！初次见面！？（{Bot_NICKNAME}被吓到但是对你的好感度+{pt}）'
            elif tag == "not_like":
                pt0 = random.randint(30,60)
                customer["love"] += pt0
                pt1 = random.randint(30,60)
                customer["happy"] += pt1
                return f'诶？...（{Bot_NICKNAME}看起来有点失落，好感度-{pt0}，心情-{pt1}）'
            elif tag == "not_love":
                pt = random.randint(20,40)
                customer["happy"] -= pt
                return f'好吧...初次见面...（{Bot_NICKNAME}看起来有点失落，心情-{pt}）'
            elif tag in ("ask_selfname","whatis_self","ask_self"):
                return f'你好！我是{Bot_NICKNAME}初次见面！（一本正经的自我介绍~）'
            elif tag in ("set_selfname","set_selfis"):
                return f"我是{Bot_NICKNAME}！初次见面喵！"
            elif tag in ("set_customername","set_customeris"):
                msg = param(data,"set_selfname",{"y"})
                if msg:
                    return f"{msg}，初次见面喵！"
                else:
                    return ["果咩...没有听懂。", f"嗯...~初次见面喵，我是{Bot_NICKNAME}",f"({Bot_NICKNAME}没有理解你的名字)"]
            elif tag in ("ask_customername","whatis_customer","whatis_other"):
                return f"诶？初次见面嘛...咱对你还不是很了解哦OvO"
            elif tag in ("wait_like","wait_love","wait_like_re","wait_love_re"):
                return ['诶？咱...好吧！',"爱你喵！"]
            else:
                return None
        else:
            self.action(customer,data)
            tag = customer["todo"]
            done = customer["done"][:-1]
            if tag == "hello":
                return self.hello().normal(customer)
            elif tag == "like":
                if "not_like" in done or "not_love" in done:
                    return self.like().difficult(customer)
                else:
                    return self.like().normal(customer)
            elif tag == "love":
                if "not_like" in done or "not_love" in done:
                    return self.love().difficult(customer)
                else:
                    return self.love().normal(customer)
            elif tag == "unfriendly":
                return self.negative().unfriendly(customer)
            elif tag == "not_like":
                return self.negative().not_like(customer)
            elif tag == "not_love":
                return self.negative().not_love(customer)
            elif tag == "wait_like":
                if "not_like" in done or "not_love" in done:
                    return self.wait_like().difficult(customer)
                else:
                    return self.wait_like().normal(customer)
            elif tag == "wait_like_re":
                if "not_like" in done or "not_love" in done:
                    return self.wait_like().difficult_reply(customer)
                else:
                    return self.wait_like().reply(customer)
            elif tag == "wait_love":
                if "not_like" in done or "not_love" in done:
                    return self.wait_love().difficult(customer)
                else:
                    return self.wait_love().normal(customer)
            elif tag == "wait_love_re":
                if "not_like" in done or "not_love" in done:
                    return self.wait_love().difficult_reply(customer)
                else:
                    return self.wait_love().reply(customer)
            elif tag == "ask_selfname":
                if "ask_selfname" in done:
                    return self.ask_selfname().repeat(customer)
                elif "set_selfname" in done:
                    return self.ask_selfname().new(customer)
                else:
                    return self.ask_selfname().normal(customer)
            elif tag == "ask_customername":
                if "set_customername" in done:
                    return self.ask_customername().repeat(customer)
                elif "ask_customername" in done:
                    return self.ask_customername().new(customer)
                else:
                    return self.ask_customername().normal(customer)
            elif tag == "set_selfname":
                if "set_selfname" in done:
                    return self.set_selfname().repeat(customer, data)
                else:
                    return self.set_selfname().normal(customer, data)
            elif tag == "set_customername":
                if "set_customername" in done:
                    return self.set_customername().repeat(customer, data)
                else:
                    return self.set_customername().normal(customer, data)
            elif tag == "set_customername":
                if "set_customername" in done:
                    return self.set_customername().repeat(customer, data)
                else:
                    return self.set_customername().normal(customer, data)
            elif tag == "set_selfis":
                return self.memory().set_selfis(customer, data)
            elif tag == "whatis_self":
                return self.memory().whatis_self(customer, data)
            elif tag == "set_customeris":
                return self.memory().set_customeris(customer, data)
            elif tag == "whatis_customer":
                return self.memory().whatis_customer(customer, data)
            elif tag == "set_otheris":
                return self.memory().set_otheris(customer, data)
            elif tag == "whatis_other":
                return self.memory().whatis_other(customer, data)

    class hello():
        def __init__(self):
            self.replay_data = lika.replay_data["hello"]

        def normal(self, customer: dict):
            """
            你好！
            """
            msg = lika.replay(customer, self.replay_data["normal"], False)
            return msg

    class like():
        def __init__(self):
            self.replay_data = lika.replay_data["like"]

        def normal(self, customer: dict):
            """
            喜欢你！
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                if random.randint(0,1):
                    customer["love"] += pt
                    log = f"好感度+{pt}"
                else:
                    customer["happy"] += pt
                    log = f"心情+{pt}"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def difficult(self, customer: dict):
            """
            喜欢你！（闹别扭）
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                customer["happy"] += random.randint(2*pt,4*pt)
                log = f"心情+{pt}"
                lika.save.customer_data()
            else:
                log = ""
            msg = lika.replay(customer, self.replay_data["difficult"])
            if log:
                msg = msg + f"（{log}）"

            return msg

    class love():
        def __init__(self):
            self.replay_data = lika.replay_data["love"]

        def normal(self, customer: dict):
            """
            爱你！
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                pt0 = random.randint(pt,2*pt)
                customer["love"] += pt0
                pt1 = random.randint(pt,2*pt)
                customer["happy"] += pt1
                log = f"好感度+{pt0}，心情+{pt1}"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def difficult(self, customer: dict):
            """
            爱你！（闹别扭）
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                customer["love"] += random.randint(2*pt,4*pt)
                log = f"好感度+{pt}"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["difficult"])
            if log:
                msg = msg + f"（{log}）"

            return msg

    class negative():
        def __init__(self):
            self.replay_data = lika.replay_data["love"]

        def unfriendly(self, customer: dict):
            """
            不友好。
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                pt0 = random.randint(pt,2*pt)
                customer["love"] += pt0
                pt1 = random.randint(pt,2*pt)
                customer["happy"] += pt1
                log = f"好感度+{pt0}，心情+{pt1}"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def not_like(self, customer: dict):
            """
            不喜欢你了。
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                pt0 = random.randint(pt,2*pt)
                customer["love"] += pt0
                pt1 = random.randint(pt,2*pt)
                customer["happy"] += pt1
                log = f"好感度+{pt0}，心情+{pt1}"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def not_love(self, customer: dict):
            """
            不爱你了。
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] = 0
                pt0 = random.randint(pt,2*pt)
                customer["love"] += pt0
                pt1 = random.randint(pt,2*pt)
                customer["happy"] += pt1
                log = f"好感度+{pt0}，心情+{pt1}"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

    class wait_like():
        def __init__(self):
            self.replay_data = lika.replay_data["wait_like"]

        def normal(self, customer: dict):
            """
            说喜欢我！
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] -= 1
                customer["happy"] += 1
                log = "心情+1"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def difficult(self, customer: dict):
            """
            说喜欢我！（闹别扭）
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] -= 1
                customer["happy"] += 2
                log = "心情+2"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["difficult"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def reply(self, customer: dict):
            """
            喜欢我吗？
            """
            msg = lika.replay(customer, self.replay_data["reply"])
            return msg

        def difficult_reply(self, customer: dict):
            """
            喜欢我吗？（闹别扭）
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] -= 2
                customer["happy"] += 2
                log = "心情+1"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["difficult_reply"])
            if log:
                msg = msg + f"（{log}）"

            return msg

    class wait_love():
        def __init__(self):
            self.replay_data = lika.replay_data["wait_love"]

        def normal(self, customer: dict):
            """
            说爱我！
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] -= 1
                customer["love"] += 1
                log = "好感度+1"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["normal"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def difficult(self, customer: dict):
            """
            说爱我！（闹别扭）
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] -= 1
                customer["love"] += 2
                log = "好感度+2"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["difficult"])
            if log:
                msg = msg + f"（{log}）"

            return msg

        def reply(self, customer: dict):
            """
            爱我嘛？
            """
            msg = lika.replay(customer, self.replay_data["reply"])
            return msg

        def difficult_reply(self, customer: dict):
            """
            爱我嘛？（闹别扭）
            """
            pt = customer["lika"]
            if pt > 0:
                customer["lika"] -= 2
                customer["love"] += 2
                log = "好感度+1"
                lika.save.customer_data()
            else:
                log = ""

            msg = lika.replay(customer, self.replay_data["difficult_reply"])
            if log:
                msg = msg + f"（{log}）"

            return msg

    class ask_selfname():
        def __init__(self):
            self.replay_data = lika.replay_data["ask_selfname"]

        def normal(self, customer: dict):
            """
            你叫什么名字！
            """
            msg = lika.replay(customer, self.replay_data["normal"])
            return msg

        def repeat(self, customer: dict):
            """
            你叫什么名字！重复
            """
            msg = lika.replay(customer, self.replay_data["repeat"])
            return msg

        def new(self, customer: dict):
            """
            你叫什么名字！新名字
            """
            msg = lika.replay(customer, self.replay_data["new"])
            return msg

    class ask_customername():
        def __init__(self):
            self.replay_data = lika.replay_data["ask_customername"]

        def normal(self, customer: dict):
            """
            我叫什么名字！
            """
            msg = lika.replay(customer, self.replay_data["normal"])
            return msg

        def repeat(self, customer: dict):
            """
            我叫什么名字！重复
            """
            msg = lika.replay(customer, self.replay_data["repeat"])
            return msg

        def new(self, customer: dict):
            """
            我叫什么名字！新名字
            """
            msg = lika.replay(customer, self.replay_data["new"])
            return msg

    class set_selfname():
        def __init__(self):
            self.replay_data = lika.replay_data["set_selfname"]

        def save(self, customer: dict, data: dict) -> bool:
            msg = param(data,"set_selfname",{"y"})
            if msg:
                customer["nickname"] = msg
                lika.save.customer_data()
                return True
            else:
                return False

        def normal(self, customer: dict, data: dict):
            """
            就叫你小叶子吧！
            """
            self.save(customer, data)
            msg = lika.replay(customer, self.replay_data["normal"])
            return msg

        def repeat(self, customer: dict, data: dict):
            """
            就叫你小叶子吧！重复
            """
            self.save(customer, data)
            msg = lika.replay(customer, self.replay_data["repeat"])
            return msg

    class set_customername():
        def __init__(self):
            self.replay_data = lika.replay_data["set_customername"]

        def save(self, customer: dict, data: dict):
            msg = param(data,"set_customername",{"y"})
            if msg:
                customer["customer"]["nickname"] = msg
                lika.save.customer_data()
                return True
            else:
                return False

        def normal(self, customer: dict, data: dict):
            """
            以后要叫我主人哦！
            """
            self.save(customer, data)
            msg = lika.replay(customer, self.replay_data["normal"])
            return msg

        def repeat(self, customer: dict, data: dict):
            """
            以后要叫我主人哦！重复
            """
            self.save(customer, data)
            msg = lika.replay(customer, self.replay_data["repeat"])
            return msg

    class memory():
        def __init__(self):
            self.replay_data = lika.replay_data["memory"]

        def set_selfis(self, customer: dict, data: dict):
            """
            你是我老婆。
            """
            customer["title"] = param(data["param"].get("set_selfis"))
            msg = lika.replay(customer, self.replay_data["set_selfis"])
            return msg

        def whatis_self(self, customer: dict, data: dict):
            """
            你是什么人？
            """
            TITLE = customer["title"]
            if title:
                msg = lika.replay(customer, self.replay_data["whatis_self"])
            else:
                msg = lika.replay(customer, self.replay_data["unknow"])

            return msg.replace("TITLE",TITLE)

        def set_customeris(self, customer: dict, data: dict):
            """
            我是你的老公！
            """
            customer["customer"]["title"] = param(data["param"].get("set_customeris")) 
            msg = lika.replay(customer, self.replay_data["set_customeris"])
            return msg

        def whatis_customer(self, customer: dict, data: dict):
            """
            我是什么人
            """
            TITLE = customer["title"]
            if title:
                msg = lika.replay(customer, self.replay_data["whatis_customer"])
            else:
                msg = lika.replay(customer, self.replay_data["unknow"])

            return msg.replace("TITLE",TITLE)

        def set_otheris(self, customer: dict, data: dict):
            """
            枫枫是机器人。
            """
            key = param(data,data["param"].get("set_otheris")[0][1])
            value = param(data,"set_otheris")
            customer["memory"].update({key:value})
            lika.save.customer_data()
            NAME1 = customer["nickname"] or Bot_NICKNAME
            NAME2 = lika.nickname(customer)
            return f"{key}是{value}".replace("NAME1", NAME1).replace("NAME2", NAME2)

        def whatis_other(self, customer: dict, data: dict):
            """
            枫枫是谁。
            """
            key = param(data,data["param"].get("whatis_other")[0][1]) or param(data,"whatis_other")
            value = customer["memory"].get(key)
            if value:
                NAME1 = customer["nickname"] or Bot_NICKNAME
                NAME2 = lika.nickname(customer)
                return f"{key}是{value}".replace("NAME1", NAME1).replace("NAME2", NAME2)
            else:
                return f"{Bot_NICKNAME}不知道哦。"

    class hello1():
        def __init__(self):
            self.replay_data = lika.replay_data["hello"]
        def normal(self, customer: dict):
            """
            你好！
            """
            msg = lika.replay(customer, self.replay_data["normal"])
            return msg

    class hello1():
        def __init__(self):
            self.replay_data = lika.replay_data["hello"]
        def normal(self, customer: dict):
            """
            你好！
            """
            msg = lika.replay(customer, self.replay_data["normal"])
            return msg

lika = Manager()