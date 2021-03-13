import time
from abc import ABC, abstractmethod

import pathlib

import config


class BaseHttpResponse(ABC):
    def __init__(self):
        self.headers = None
        self.body = None
        self.content_type = None
        self.content_length = 0

        self._generate_response_headers()

    def _generate_response_headers(self):
        if self.body is not None:
            self.content_length = len(self.body)

        self.headers = f"HTTP/{config.HTTP_VERSION} {self.status}\r\n" + \
                       f"Server: {config.SERVER_NAME}\r\n" + \
                       f"Date: {time.strftime('%c')}\r\n" + \
                       f"Connection: Close\r\n" + \
                       f"Content-Length: {self.content_length}\r\n" + \
                       f"Content-Type: {self.content_type}\r\n\r\n"

    @property
    @abstractmethod
    def status(self):
        pass

    def encode(self):
        if self.body is None:
            return self.headers.encode()
        else:
            return self.headers.encode() + self.body

    def __str__(self):
        return self.headers


class HttpResponseBadResponse(BaseHttpResponse):
    status = "400 Bad Request"


class HttpResponseForbidden(BaseHttpResponse):
    status = "403 Forbidden"


class HttpResponseNotFound(BaseHttpResponse):
    status = "404 Not Found"


class HttpResponseMethodNotAllowed(BaseHttpResponse):
    status = "405 Method Not Allowed"


class HttpResponseOK(BaseHttpResponse):
    status = "200 OK"

    def __init__(self, body, filename, with_body=True):
        super().__init__()

        if with_body:
            self.body = body

        self.content_length = len(body)

        self._get_content_type_by_filename(filename)

        self._generate_response_headers()

    def _get_content_type_by_filename(self, filename):
        if filename is None:
            return

        extinction = pathlib.Path(filename).suffix
        self.content_type = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.swf': 'application/x-shockwave-flash',
        }.get(extinction)
