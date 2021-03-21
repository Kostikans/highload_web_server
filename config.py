import pathlib

from server.config_parser import parse_config

config = parse_config('/etc/httpd.conf')

HTTP_VERSION = 1.1
HTTP_ACCEPTABLE = ["HTTP/1.0", "HTTP/1.1"]
METHODS_ACCEPTABLE = ["GET", "HEAD"]
SERVER_NAME = ["KOSTIKAN HIGHLOAD WEBSERVER"]
ADDRESS = "localhost"
PORT = 80
MEDIA_FOLDER_NAME = "httptest"

PROJECT_ROOT = pathlib.Path(config.get("document_root", pathlib.Path(__file__).parent.absolute()))
MEDIA_ROOT = PROJECT_ROOT.joinpath(MEDIA_FOLDER_NAME)
CPU_LIMIT = int(config.get("cpu_limit"))
MAX_CONNECTIONS = 500