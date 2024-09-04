from collections.abc import Coroutine, Callable, MutableMapping, Sequence
from typing import overload
from pathlib import Path
import urllib.parse
from .response import Response

type AvailableRoutePath = str | Path | list[str] | RoutePath


class RoutePathError(Exception):
    pass


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

    def __bool__(self) -> bool:
        return bool(self._data)

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

    def route_to(self, key: str) -> "RouteMap":
        """
        获取子路由
        """
        if key not in self._data:
            raise RoutePathError(f"'{key}' are not exist in this routemap")
        return self._data[key]

    def set_route(self, path: AvailableRoutePath, route_map: "RouteMap | None" = None) -> "RouteMap":
        """
        设置路由
            path: 路径: 在设置路径中, 如果路径中包含 {xxx} 则会自动匹配路由
            route_map: 设置此节点子路由，为空则是空路由
        """
        if not isinstance(path, RoutePath):
            path = RoutePath(path)
        if not path:
            if route_map:
                for k, v in vars(route_map).items():
                    setattr(self, k, v)
            return self
        node: RouteMap = self
        for key in path[:-1]:
            if key in node._data:
                node = node._data[key]
            else:
                node = node._data[key] = RouteMap()
        node = node._data[path[-1]] = route_map or RouteMap()
        return node

    def router(self, path: AvailableRoutePath = "/", **kwargs):
        if isinstance(path, str):
            node = self
            for x in path.strip("/").split("/"):
                if not x:
                    continue
                if x.startswith("{") and x.endswith("}"):
                    kwargs["keyword"] = x[1:-1]
                    key = "{id}"
                else:
                    key = urllib.parse.quote(x)
                if key in node._data:
                    node = node._data[key]
                else:
                    node = node._data[key] = RouteMap()

        def decorator(func: Callable[..., Coroutine]):
            node.app = func

        return decorator

    def redirect(self, code: int, path: AvailableRoutePath, redirect_to: str):
        """
        301 Moved Permanently 永久移动

        302 Found 临时移动

        303 See Other 其他地址

        307 Temporary Redirect 临时重定向

        308 Permanent Redirect 永久重定向
        """
        route_map = self.set_route(path)
        route_map.response = Response(code, [(b"Location", redirect_to.encode(encoding="utf-8"))])

    for_router: set[str] = set()
    for_response: set[str] = {".html", ".js", ".txt", ".json"}

    def directory(
        self,
        src_path: Path | str,
        html: bool = False,
        for_router: set = for_router,
        for_response: set = for_response,
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

        for inner_src_path in src_path.iterdir():
            key = urllib.parse.quote(str(inner_src_path.as_posix()).strip("/").split("/")[-1])
            is_dir = inner_src_path.is_dir()
            route_map = self[key] = RouteMap(is_dir=is_dir)
            if is_dir:
                route_map.directory(inner_src_path, html)
                continue

            route_map.file(inner_src_path, for_router=for_router, for_response=for_response)

            if html and inner_src_path.name == "index.html":
                self.app = route_map.app
                self.response = route_map.response

    def file(
        self,
        src_path: Path,
        for_router: set = for_router,
        for_response: set = for_response,
    ):
        if for_router:
            if src_path.suffix in self.for_router:
                self.file_for_router(src_path)
            else:
                self.file_for_response(src_path)
        elif for_response:
            if src_path.suffix in self.for_response:
                self.file_for_response(src_path)
            else:
                self.file_for_router(src_path)
        else:
            self.file_for_router(src_path)

    def file_for_router(self, src_path: Path):
        async def func(scope, receive):
            with open(src_path, "rb") as f:
                return Response(
                    code=200,
                    headers=Response.content_type(src_path.suffix),
                    bodys=[f.read()],
                )

        self.app = func

    def file_for_response(self, src_path: Path):
        with open(src_path, "rb") as f:
            self.response = Response(
                code=200,
                headers=Response.content_type(src_path.suffix),
                bodys=[f.read()],
            )
