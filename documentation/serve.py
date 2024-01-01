import http.server

from pathlib import Path

site_dir = Path(Path(__file__).parent.parent, "docs")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=site_dir, **kwargs)


server = http.server.HTTPServer(("127.0.0.1", 8000), Handler)
print("Serving HTTP on 127.0.0.1 port 8000 (http://127.0.0.1:8000/) ...")
server.serve_forever()
