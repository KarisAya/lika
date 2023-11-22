# Lika
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

## 开始使用

当然你的web服务器里面要有内容

```python
server = Server()
root = server.router_map
```
root是你的web服务器根目录

## router_map.mount
你可以添加一些资源
```python
root.mount("./src", True)
```
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
那么访问 http://127.0.0.1:8080/image/07c438ee01fc3bbeb21a116f2ad1e440.png

你将会看到这张图片

_ps:

访问 http://127.0.0.1:8080/index/

你将会看到 /index/index.html

除非你用 root.mount("./src", False) 

这样添加的本地资源不会使文件夹对应文件夹下的index.html_



# 📖 介绍



# 📝 更新日志
