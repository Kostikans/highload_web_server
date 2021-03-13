import pathlib

from server.config_parser import parse_config

config = parse_config('httpd.conf')

HTTP_VERSION = 1.1
HTTP_ACCEPTABLE = ["HTTP/1.0", "HTTP/1.1"]
METHODS_ACCEPTABLE = ["GET", "HEAD"]
SERVER_NAME = ["KOSTIKAN HIGHLOAD WEBSERVER"]
ADDRESS = "localhost"
PORT = 80