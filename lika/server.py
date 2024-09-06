from .router import RouteMap, WILDCARD
from .response import Response
import urllib.parse


class Server:
    def __init__(self):
        self.route_map: RouteMap = RouteMap()
        self.NotFound: Response = Response(404)

    async def __call__(self, scope, receive, send):
        data = self.find_route(scope["path"])
        if data is None:
            response = self.NotFound
        else:
            node, kwargs = data
            response = await node(scope, receive, **kwargs)
        if response is None:
            response = self.NotFound
        await send(response.start)
        for body in response.bodys:
            await send(body)

    def find_route(self, path: str):
        node = self.route_map
        kwargs = {}
        for key in urllib.parse.unquote(path).strip("/").split("/"):
            if key == WILDCARD:
                return
            if key in node:
                node = node[key]
            elif WILDCARD in node:
                node = node[key]
                kwargs[node.keyword] = key
            else:
                return
            node = node[key]
        return node, kwargs


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
