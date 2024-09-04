from collections.abc import Coroutine, Callable, MutableMapping, Sequence
from typing import overload
from pathlib import Path
import urllib.parse
from .response import Response

type AvailableRoutePath = str | Path | list[str] | RoutePath


class RoutePath(Sequence[str]):
    _data: list[str]

    def __len__(self):
        return len(self._data)

    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> list[str]: ...

    def __getitem__(self, index: int | slice):
        return self._data[index]

    def __setitem__(self, index: int, value: str):
        self._data[index] = value

    def __iter__(self):
        return iter(self._data)

    def __init__(self, data: AvailableRoutePath):
        if isinstance(data, RoutePath):
            self._data = data._data
            return
        if isinstance(data, Path):
            result = urllib.parse.quote(str(data.as_posix())).strip("/").split("/")
        elif isinstance(data, str):
            result = urllib.parse.quote(data.replace("\\", "/")).strip("/").split("/")
        elif isinstance(data, list):
            if not all(isinstance(x, str) for x in data):
                raise TypeError(f"{data} is not a valid path")
            result = data
        else:
            raise TypeError(f"{data} is not a valid path")
        self._data = result[1:] if result and result[0] == "" else result

    def __add__(self, other: AvailableRoutePath):
        if isinstance(other, RoutePath):
            return RoutePath(self._data + other._data)
        else:
            return RoutePath(self._data + RoutePath(other)._data)

    def __radd__(self, other: AvailableRoutePath):
        if isinstance(other, RoutePath):
            return other + self
        else:
            return RoutePath(other) + self

    @property
    def url(self) -> str:
        return "".join(f"/{x}" for x in self) or "/"

    @property
    def path(self) -> str:
        return urllib.parse.unquote(self.url)

    @property
    def name(self) -> str:
        return urllib.parse.unquote((self or ["/"])[-1])


class RouteMap(MutableMapping[str, "RouteMap"]):
    _data: dict[str, "RouteMap"]
    app: Callable[..., Coroutine] | None = None

    def __getitem__(self, key: str) -> "RouteMap":
        return self._data[key]

    def __setitem__(self, key: str, value: "RouteMap"):
        self._data[key] = value

    def __delitem__(self, key: str):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        repr = {}
        repr["response"] = bool(self.response)
        repr["app"] = bool(self.app)
        repr["keyword"] = self.keyword
        repr["map"] = self._data
        return repr.__repr__()

    def __init__(
        self,
        is_dir: bool = True,
        response: Response | None = None,
        keyword: str | None = None,
    ):
        self._data = {}
        self.is_dir = is_dir
        self.response = response
        self.keyword = keyword
        self.kwargs = {}

    async def __call__(self, scope, receive, send, **kwargs):
        """
        执行 ASGI 发送方法
        """
        if self.app is None:
            response = self.response or Response(404)
        else:
            response = await self.app(scope, receive, **kwargs)
        await send(response.start)
        for body in response.bodys:
            await send(body)

    def route_to(self, key: str, /, **kwargs) -> "RouteMap":
        """
        获取子路由
        """
        if key not in self._data:
            self._data[key] = RouteMap(**kwargs)
        return self._data[key]

    def set_route(self, path: AvailableRoutePath, route_map: "RouteMap | None" = None, /, **kwargs) -> "RouteMap":
        """
        设置路由
            path: 路径: 在设置路径中, 如果路径中包含 {xxx} 则会自动匹配路由
            route_map: 设置此节点子路由，为空则是空路由
        """
        if not isinstance(path, RoutePath):
            path = RoutePath(path)
        node = self
        for k in path[:-1]:
            node = node.route_to(k, **kwargs)
        k = path[-1]
        if route_map:
            node = node._data[k] = node
        else:
            node = node.route_to(k, **kwargs)
        return node

    def router(self, path: AvailableRoutePath = "/", **kwargs):
        if isinstance(path, str):
            node = self
            for x in path.strip("/").split("/"):
                if x.startswith("{") and x.endswith("}"):
                    kwargs["keyword"] = x[1:-1]
                    k = "{id}"
                else:
                    k = urllib.parse.quote(x)
                node = node.route_to(k, **kwargs)

        else:
            node = self.set_route(path)

        def decorator(func: Callable[..., Coroutine]):
            async def warpper(scope, receive, **kwargs):
                return await func(scope, receive, **kwargs)

            node.app = warpper

        return decorator

    def redirect(self, code: int, path: AvailableRoutePath, redirect_to: str):
        route_map = self.set_route(path)
        route_map.response = Response(code, [(b"Location", redirect_to.encode())])

    def directory(
        self,
        src_path: Path | str,
        html: bool = False,
        for_router: set = set(),
        for_response: set = {".html", ".js", ".txt", ".json"},
    ):
        """
        把文件夹作为路由
            src_path: 路由文件夹路径
            html: 根目录默认为此目录下 index.html
            for_router: 动态响应文件后缀
            for_response: 静态响应文件后缀
        """
        if isinstance(src_path, str):
            src_path = Path(src_path)
        for src_sp in src_path.iterdir():
            k = RoutePath(src_sp)[-1]
            route_map = self[k] = RouteMap(src_sp.is_dir())
            if route_map.is_dir:
                route_map.directory(src_sp, html)
                continue
            route_map.file(src_path, for_router, for_response)
            if html and src_sp.name == "index.html":
                self.app = route_map.app
                self.response = route_map.response

    def file(self, src_path: Path, for_router: set, for_response: set):
        if for_router:
            if src_path.suffix in for_router:
                self.file_for_router(src_path)
            else:
                self.file_for_response(src_path)
        elif for_response:
            if src_path.suffix in for_response:
                self.file_for_response(src_path)
            else:
                self.file_for_router(src_path)
        else:
            self.file_for_router(src_path)

    def file_for_router(self, src_path: Path):
        @self.router()
        async def _(scope, receive):
            with open(src_path, "rb") as f:
                response = Response(
                    code=200,
                    headers=Response.content_type(src_path.suffix),
                    bodys=[f.read()],
                )
                return response

    def file_for_response(self, src_path: Path):
        with open(src_path, "rb") as f:
            self.response = Response(
                code=200,
                headers=Response.content_type(src_path.suffix),
                bodys=[f.read()],
            )
