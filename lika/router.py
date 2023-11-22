from typing import List, Dict
from pathlib import Path
import urllib.parse


class RouterPath(List[str]):
    def __init__(self, data):
        super().__init__()
        if isinstance(data, Path):
            result = urllib.parse.quote(str(data.as_posix())).strip("/").split("/")
        elif isinstance(data, str):
            result = urllib.parse.quote(data.replace("\\", "/")).strip("/").split("/")
        else:
            result = data
        self.extend(result[1:] if result and result[0] == "" else result)

    def __add__(self, other):
        return RouterPath(super().__add__(RouterPath(other)))

    def __radd__(self, other):
        return RouterPath(RouterPath(other) + self)

    @property
    def url(self) -> str:
        return "".join(f"/{x}" for x in self) or "/"

    @property
    def path(self) -> str:
        return urllib.parse.unquote(self.url)

    @property
    def name(self) -> str:
        return urllib.parse.unquote((self or ["/"])[-1])
