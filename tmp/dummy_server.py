import http.server
import socketserver

class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        print(f"OPTIONS received! Headers:\n{self.headers}")
        self.send_response(200)
        self.end_headers()

with socketserver.TCPServer(("", 8000), Handler) as httpd:
    print("Serving at port 8000")
    httpd.serve_forever()
