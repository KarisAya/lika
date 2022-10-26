import sys

sys.path.append('D:/testbot/src/plugins/lika')

import time

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from utils import analys, analys_text, analys_list,analys_seg

if __name__ == "__main__":
    a = "hello"
    print(a[:2]=="he")
    for i in []:
        print("Hello_World")
if __name__ == "__main__":
    msg = []
    msg.append("就叫你小叶子吧")
    msg.append("请问我可以叫你小叶子吗?")
    msg.append("我可以叫你小叶子吗")
    msg.append("现在你就叫我文酱吧")
    msg.append("我也喜欢你")
    msg.append("那你应该叫我什么")
    msg.append("叫我玩原神的吧u")
    msg.append('你是谁，我是谁，小叶子是谁,   小叶子是你的姐姐， 斯佩是我老婆,你叫什么名字？我是糖糖！糖糖你好，你是我老婆。你好。')
    for x in msg:
        data = analys(x)
        print(f"\n\n原句：{x}\n")
        # print("\n标签：",analys_list(analys_text(x)))
        print("\n分析：", json.dumps(data, ensure_ascii = False, indent = 4))
        # i = 1
        # for key in data["param"].keys():
        #     if key == "start" or key.startswith("cut"):
        #         continue
        #     else:
        #         A,B = analys_seg(data["param"][key])
        #         if B:
        #             B = analys_seg(data["param"][B])[0]
        #         print(
        #             f"事件{i}：{key}\n"
        #             f"参数A：{A}\n"
        #             f"参数B：{B}"
        #         )
        #         i += 1
        #         if key.startswith("learn"):
        #             print(f"\n回应：{B}是{A}")
        #         print(f"\n")
    input()