from .router import RouteMap
from .response import Response


class Server:
    def __init__(self):
        self.route_map: RouteMap = RouteMap()
        self.error = RouteMap()
        for i in range(400, 419):
            self.error[str(i)] = RouteMap()

    async def __call__(self, scope, receive, send):
        node = self.route_map
        path: str = scope["path"]
        kwargs = {}
        for k in path.strip("/").split("/"):
            if not k:
                continue
            if k in node:
                node = node[k]
            elif "{id}" in node:
                node = node["{id}"]
                assert node.keyword is not None
                kwargs[node.keyword] = k
            else:
                response = await self.error["404"](scope, receive)
                break
        else:
            response = await node(scope, receive, **kwargs)
            if not response:
                response = await self.error["404"](scope, receive)

        assert isinstance(response, Response)

        await send(response.start)
        for body in response.bodys:
            await send(body)


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
