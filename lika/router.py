from collections.abc import Coroutine, Callable, MutableMapping, Sequence
from typing import overload
from pathlib import Path
import urllib.parse
from .response import Response

WILDCARD = r"{id}"

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
        elif isinstance(data, Path):
            data = data.as_posix().strip("/").split("/")
        elif isinstance(data, str):
            data = data.replace("\\", "/").strip("/").split("/")
        elif isinstance(data, list):
            if not all(isinstance(x, str) for x in data):
                raise TypeError(f"{data} is not a valid path")
        else:
            raise TypeError(f"{data} is not a valid path")
        self._data = [x for x in data if x]

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
        return urllib.parse.quote(self.path)

    @property
    def path(self) -> str:
        return "".join(f"/{x}" for x in self) or "/"

    @property
    def name(self) -> str:
        try:
            return self[-1]
        except IndexError:
            return "/"


class RouteMap(MutableMapping[str, "RouteMap"]):
    _data: dict[str, "RouteMap"]
    app: Callable[..., Coroutine[None, None, Response | None]] | None = None

    def __getitem__(self, key: str) -> "RouteMap":
        try:
            return self._data[key]
        except KeyError:
            raise RoutePathError(f"{key} are not exist")

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

    async def __call__(self, scope, receive, /, **kwargs):
        """
        执行 ASGI 发送方法
        """
        if self.app is None:
            response = self.response
        else:
            response = await self.app(scope, receive, **kwargs)
        return response

    def find_route(self, route_path: RoutePath):
        """
        查找路由
        """
        node = self
        for key in route_path:
            node = node[key]
        return node

    def create_route(self, route_path: AvailableRoutePath):
        """
        创建路由
        """
        node = self
        for key in RoutePath(route_path):
            if key in node:
                node = node[key]
            elif WILDCARD in node:
                node = node[key]
            else:
                if key.startswith("{") and key.endswith("}"):
                    keyword = key[1:-1]
                    key = WILDCARD
                else:
                    keyword = None
                node[key] = RouteMap(keyword=keyword)
                node = node[key]
        return node

    def router(self, route_path: AvailableRoutePath = "/"):
        node = self.create_route(route_path)

        def decorator(func: Callable[..., Coroutine]):
            node.app = func

        return decorator

    def redirect(self, code: int, route_path: AvailableRoutePath, redirect_to: str):
        """
        301 Moved Permanently 永久移动

        302 Found 临时移动

        303 See Other 其他地址

        307 Temporary Redirect 临时重定向

        308 Permanent Redirect 永久重定向
        """
        self.create_route(route_path).response = Response(code, [(b"Location", redirect_to.encode(encoding="utf-8"))])

    for_router: set[str] = set()
    for_response: set[str] = {".html", ".js", ".txt", ".json"}

    def directory(
        self,
        src_path: Path | str,
        html: bool = False,
    ):
        """
        把文件夹作为路由
            src_path: 路由文件夹路径
            html: 根目录默认为此目录下 index.html
        """
        if isinstance(src_path, str):
            src_path = Path(src_path)

        for inner_src_path in src_path.iterdir():
            key = inner_src_path.name
            is_dir = inner_src_path.is_dir()
            route_map = self[key] = RouteMap(is_dir=is_dir)
            if is_dir:
                route_map.directory(inner_src_path, html)
                continue
            route_map.file(inner_src_path)
            if html and inner_src_path.name == "index.html":
                self.app = route_map.app
                self.response = route_map.response

    def file(
        self,
        src_path: Path,
    ):
        if self.for_router:
            if src_path.suffix in self.for_router:
                self.file_for_router(src_path)
            else:
                self.file_for_response(src_path)
        elif self.for_response:
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
