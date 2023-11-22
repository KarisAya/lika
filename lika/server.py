from typing import Literal
from .router import RouterPath, RouterMap


Env = Literal["dev", "test", "prod"]


class Server:
    def __init__(self, env: Env = "dev"):
        self.router_map = RouterMap()
        self.error = RouterMap()
        for i in range(400, 419):
            self.error[str(i)] = RouterMap()

    def get_map(self, path: str) -> RouterMap:
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
