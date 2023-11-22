from typing import Coroutine, Callable, Literal, Any, Type, Dict, Tuple
from pathlib import Path


from .response import Response, Headers
from .router import RouterPath


Env = Literal["dev", "test", "prod"]


class RouterMap(Dict[str, "RouterMap"]):
    app: Coroutine = None
    response: Response = None
    keyword: str = ""

    def __init__(
        self,
        is_file: bool = False,
        response: Response = Response(404),
    ):
        super().__init__()
        self.is_file = is_file
        self.response = response
        self.kwargs = {}

    async def __call__(self, scope, receive, send, **kwargs):
        """
        执行 ASGI 发送方法
        """
        if self.app:
            response = await self.app(scope, receive, **kwargs)
        else:
            response = self.response
        await send(response.start)
        for body in response.bodys:
            await send(body)

    def set_map(self, path: RouterPath, router_map: "RouterMap" = None) -> "RouterMap":
        """
        占位地址：{id}
        """
        return_map = self
        path = RouterPath(path)
        for k in path:
            if k.startswith("%7B") and k.endswith("%7D"):
                return_map = return_map.setdefault("{id}", RouterMap())
                return_map.keyword = k[3:-3]
            else:
                return_map = return_map.setdefault(k, RouterMap())
        if not router_map is None:
            for name, v in vars(router_map).items():
                setattr(return_map, name, v)
            return_map.update(router_map)
        return return_map

    def get_map(self, path: RouterPath) -> "RouterMap":
        router_map = self
        for k in RouterPath(path):
            if k in router_map:
                router_map = router_map[k]
            elif "{id}" in router_map:
                router_map = router_map["{id}"]
            else:
                return None
        return router_map

    def router(self, path: RouterPath = "/", **kwargs) -> Callable:
        router_map = self.set_map(path)

        def decorator(func):
            async def warpper(scope, receive, **others):
                others.update(kwargs)
                return await func(scope, receive, **others)

            router_map.app = warpper

        return decorator

    def redirect(self, code: int, path: RouterPath, redirect_to: str):
        router_map = self.set_map(path)
        router_map.app = None
        router_map.response = Response(code, [(b"Location", redirect_to.encode())])

    def mount(self, src_path: Path, html: bool = False):
        src_path = Path(src_path)
        for src_sp in src_path.iterdir():
            k = RouterPath(src_sp)[-1]
            router_map = self[k] = RouterMap(src_sp.is_file())
            if not router_map.is_file:
                router_map.mount(src_sp, html)
                continue

            @router_map.router(src_path=src_sp)
            async def _(scope, receive, src_path: Path):
                with open(src_path, "rb") as f:
                    response = Response(
                        code=200,
                        headers=Headers.from_ext(src_path.suffix),
                        bodys=[f.read()],
                    )
                return response

            if html and src_sp.name == "index.html":
                self.app = self[k].app

    def mount_in_memory(self, src_path: Path, html: bool = False):
        src_path = Path(src_path)
        for src_sp in src_path.iterdir():
            k = RouterPath(src_sp)[-1]
            if src_sp.is_dir():
                self[k] = RouterMap()
                self[k].mount(src_sp, html)
            else:
                self[k] = RouterMap(is_file=True)
                with open(src_sp, "rb") as f:
                    response = Response(
                        code=200,
                        headers=Headers.from_ext(src_sp.suffix),
                        bodys=[f.read()],
                    )

                self[k].response = response

                if html and src_sp.name == "index.html":
                    self.response = self[k].response


class Server:
    def __init__(self, env: Env = "dev"):
        self.router_map = RouterMap()
        self.error = RouterMap()
        for i in range(400, 419):
            self.error[str(i)] = RouterMap()

    def get_map(self, path: str) -> "RouterMap":
        router_map = self.router_map
        kwargs = {}
        for k in RouterPath(path):
            if k in router_map:
                router_map = router_map[k]
            elif "{id}" in router_map:
                router_map = router_map["{id}"]
                kwargs[router_map.keyword] = k
            else:
                return self.error["404"], kwargs
        return router_map, kwargs

    async def __call__(self, scope, receive, send):
        router_map, kwargs = self.get_map(scope["path"])
        return await router_map(scope, receive, send, **kwargs)


# def proxy(self, key: str, url: str):
#     """
#     代理
#     """
#     parsed_url = urllib.parse.urlparse(url)
#     host = parsed_url.hostname
#     port = parsed_url.port
#     path = parsed_url.path

#     def wrapper(handler: http.server.SimpleHTTPRequestHandler):
#         conn = http.client.HTTPConnection(host, port)

#         def request(network_path: str):
#             conn.request(handler.command, network_path)
#             resp = conn.getresponse()
#             if resp.status == 301:
#                 return request(resp.getheader("Location"))
#             return resp

#         resp = request(path)
#         handler.send_response(resp.status)
#         for header in resp.getheaders():
#             handler.send_header(*header)
#         handler.end_headers()
#         handler.wfile.write(resp.read())
#         conn.close()

#     self.PROXY_DICT[key] = wrapper
