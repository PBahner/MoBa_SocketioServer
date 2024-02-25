import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = "0.0.0.0"
serverPort = 8080


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            print("Pfad: ", os.path.dirname(__file__))
            if self.path == "/":
                self.path = "/index.html"
            f = open(os.path.dirname(__file__) + self.path, 'rb').read()
            if self.path == "/index.html":  # replace socketio-ipaddress
                # it is a bit tricky to get local ip address
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Connect to a server (does not have to be reachable)
                s.connect(('10.255.255.255', 1))
                local_ip = s.getsockname()[0]
                s.close()
                f = f.decode('utf-8').replace("socketio-host", local_ip).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f)
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)


def start_webserver():
    web_server = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped.")
