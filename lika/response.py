from typing import Any, Tuple, List

Bodys = List[bytes]


class Headers(List[Tuple[bytes, bytes]]):
    @staticmethod
    def from_ext(ext: str) -> "Headers":
        ext = ext.lstrip(".")
        if ext in {"html"}:
            return [(b"Content-type", b"text/html")]
        elif ext in {"js"}:
            return [(b"Content-type", b"application/javascript")]
        elif ext in {"txt", "json"}:
            return [(b"Content-type", b"text/plain")]
        elif ext in {"jpg", "png", "jpeg", "gif", "webp"}:
            return [(b"Content-type", f"image/{ext}".encode())]
        elif ext in {"mp4", "avi", "mkv", "webm"}:
            return [(b"Content-type", f"video/{ext}".encode())]
        else:
            return [
                (b"Content-type", b"application/octet-stream"),
                (b"Content-disposition", b"attachment"),
            ]


class Response:
    def __init__(
        self,
        code: int = 200,
        headers: Headers = [],
        bodys: Bodys = [b""],
    ):
        self.bodys = [
            {
                "type": "http.response.body",
                "body": body,
                "more_body": True,
            }
            for body in bodys
        ]
        self.bodys[-1]["more_body"] = False
        headers.append((b"Content-Length", str(sum(map(len, bodys)))))
        self.start = {
            "type": "http.response.start",
            "status": code,
            "headers": headers,
        }
