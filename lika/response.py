type Bodys = list[bytes]
type Headers = list[tuple[bytes, bytes]]


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
        str(sum(map(len, bodys)))
        headers.append((b"Content-Length", str(sum(map(len, bodys))).encode("utf-8")))
        self.start = {
            "type": "http.response.start",
            "status": code,
            "headers": headers,
        }

    @staticmethod
    def content_type(ext: str) -> Headers:
        match ext := ext.lstrip("."):
            case "html":
                return [(b"Content-type", b"text/html")]
            case "js":
                return [(b"Content-type", b"application/javascript")]
            case "txt" | "json":
                return [(b"Content-type", b"text/plain")]
            case "jpg" | "png" | "jpeg" | "gif" | "webp":
                return [(b"Content-type", f"image/{ext}".encode())]
            case "mp4" | "avi" | "mkv" | "webm":
                return [(b"Content-type", f"video/{ext}".encode())]
            case _:
                return [
                    (b"Content-type", b"application/octet-stream"),
                    (b"Content-disposition", b"attachment"),
                ]
