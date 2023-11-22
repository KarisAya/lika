# lika
_✨简易 Python ASGI Web框架 ✨_

<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="python">
<a href="./LICENSE"><img src="https://img.shields.io/github/license/KarisAya/lika.svg" alt="license"></a>

# 安装

使用 pip 安装已发布的最新版本

```bash
pip install lika
```
可以克隆 Git 仓库后手动安装

```bash
git clone https://github.com/KarisAya/lika.git
```
或者选择任意你喜欢的方式

# 使用

## 使用 uvicorn 运行服务

```python
from lika.server import Server
if __name__ == "__main__":
    server = Server()
    uvicorn.run(server, host="127.0.0.1", port=8080)
```

这样你就已经运行了一个 Web 服务器

## 添加路径

当然你的web服务器里面要有内容
下面是一个示例。添加一个路由返回随机图。

```python
from pathlib import Path
from lika.server import Server
from lika.response import Response, Headers

server = Server()
root = server.router_map

# root是你的web服务器根目录地址图

image_src=list(Path("./src/image").iterdir())
@root.router("/image")
async def _(scope, receive):
    image = random.choice(image_src)
    with open(image, "rb") as f:
        return Response(200, Headers.from_ext(image.suffix), [f.read()])

# /重定向到/image
root.redirect(301, "/", "/image/")
```

## 使用子目录

```python
# 添加子目录
hello = root.set_map("/hello")
@hello.router("/world")
async def _(scope, receive):
    return Response(200, [(b"Content-type", b"text/plain")], [b"hello world"])
```

等效于

```python
@root.router("/hello/world")
async def _(scope, receive):
    return Response(200, [(b"Content-type", b"text/plain")], [b"hello world"])

hello = root.get_map("/hello") # 如果在@root.router之前执行这行代码会导致 hello == None
```

## 使用本地资源

你可以添加一些资源
```python
root.mount("./src", True)

"""
"./src":src_path
    Path,本地资源路径

True: html
    bool,访问文件夹路径是否视为访问文件夹下index.html文件
"""
```bash
在根目录添加你在本地`./src`目录的资源

假设这是你的文件结构

```bash
│  favicon.ico
├─image
│      07c438ee01fc3bbeb21a116f2ad1e440.png
│      10de76b884dde180b52b20bc198f9851.jpeg
├─index
│      bundle.js
│      index.html
└─home
        bundle.js
        index.html
```
访问 `/image/07c438ee01fc3bbeb21a116f2ad1e440.png` 你将会看到这张图片。

（即便你已经把 `/image/` 做成了随机图。）

ps:

访问 `http://127.0.0.1:8080/index/`

你将会看到 `/index/index.html`

除非你用 `root.mount("./src", False)`

## 地址占位符

形如"{id}"的地址占位符

```python
@root.router("/test/{code}/{other}") 
async def _(scope, receive, code:str, other:str):
    return Response(
        int(code),
        [(b"Content-type", b"text/plain")],
        [other.encode()],
        )
```
现在你可以正常访问 `/test/418/hello` 或者 `/test/200/world`

请不要访问`/test/hello/world`，因为你不能 `int("hello")`

## 添加

# 📖 介绍



# 📝 更新日志
