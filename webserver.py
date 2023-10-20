import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep

hostName = "0.0.0.0"
serverPort = 8080


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            print("Pfad: ", os.path.dirname(__file__))
            if self.path == "/":
                self.path = "/index.html"
            f = open(os.path.dirname(__file__) + self.path, 'rb')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f.read())
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)


def start_webserver():
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
