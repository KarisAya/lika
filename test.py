import sys

sys.path.append('D:/testbot/src/plugins/lika')

from utils import analys, analys_text, analys_list,analys_param
try:
    import ujson as json
except ModuleNotFoundError:
    import json


if __name__ == "__main__":
    a = "hello"
    print(a[:2]=="he")
    for i in []:
        print("Hello_World")
if __name__ == "__main__":
    msg = []
    msg.append('我是糖糖！')
    msg.append('你是谁')
    msg.append('你叫什么名字？')
    msg.append('糖糖你好，你是我老婆')
    msg.append('斯佩是我老婆')
    msg.append('斯佩是我的老婆')
    msg.append('你也是我老婆')
    msg.append('叫爸爸')
    msg.append('小叶子是你的姐姐')
    msg.append('小叶子是谁')
    for x in msg:
        data = analys(x)
        print(
            "原句：", x,
            "\n标签：",analys_list(analys_text(x)),
            "\n分析：", json.dumps(data, ensure_ascii = False, indent = 4),
            )
        for key in data["param"].keys():
            a,b = analys_param(data,key)
            print("\n",key,a,b)