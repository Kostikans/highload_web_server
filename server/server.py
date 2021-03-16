import atexit
import select
import os
import signal
import sys
import socket
import logging

import config

from server.request.request import HttpRequest
from server.response.response import HttpResponseMethodNotAllowed, BaseHttpResponse, HttpResponseForbidden, \
    HttpResponseNotFound, HttpResponseOK, HttpResponseBadResponse


class ChildController:
    def __init__(self, pipe):
        self.is_free = True
        self.pipe = pipe

    def __repr__(self):
        return '<%s is_free=%s>' % (
            self.__class__.__name__,
            self.is_free)


class Server:
    def __init__(self):
        self.logger = logging.getLogger('main')

        self.BIND_ADDRESS = ('localhost', config.PORT)
        self.NUM_OF_CHILDS = 100
        self.MAX_CONNECTIONS = 500
        self.BACK_LOG = 10
        self.workers = []
        self.listen_sock = None

    def Run(self):
        self._Server_Loop()

    def _process_request(self, buffer: bytes) -> HttpRequest:
        self.logger.info('In buffer = ' + repr(buffer))
        raw_request = buffer.decode()
        request = HttpRequest(raw_request=raw_request)
        print(request.HTTP_VERSION, request.METHOD, request.URL, request.HEADERS)
        return request

    def _handle(self, sock):
        self.logger.info('Start to process request')

        in_buffer = b''
        while not in_buffer.endswith(b'\n'):
            in_buffer += sock.recv(1024)

        request = self._process_request(in_buffer)

        try:
            result = str(eval(in_buffer, {}, {}))
        except Exception as e:
            result = repr(e)

        if request.METHOD not in config.METHODS_ACCEPTABLE:
            response = HttpResponseMethodNotAllowed()
            self._send_response(sock, response)
            return

        if config.MEDIA_ROOT not in request.PATH.parents:
            response = HttpResponseForbidden()
            self._send_response(sock, response)
            return

        if str(request.PATH).find("/../") > 0:
            self._send_response(sock, HttpResponseForbidden())
            return

        if str(request.PATH)[len(str(request.PATH))- 1] != request.REALPATH[len(request.REALPATH) - 1] and not os.path.isdir(request.PATH):
            self._send_response(sock, HttpResponseNotFound())
            return

        if os.path.isdir(request.PATH):
            request.PATH = str(request.PATH) + "/index.html"
            if not os.path.isfile(request.PATH):
                self._send_response(sock, HttpResponseForbidden())
                return

        try:
            content = self._read_file(request.PATH)
        except Exception as e:
            logging.error(str(e))
            self._send_response(sock, HttpResponseNotFound())
            return

        response = HttpResponseOK(content, filename=request.PATH, with_body=request.METHOD != "HEAD")
        self._send_response(sock, response)

    def _read_file(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            content = f.read()
        return content

    def _send_response(self, sock, response: BaseHttpResponse):
        self.logger.info(f"Sending response:{str(response)}")
        sock.sendall(response.encode())
        self.logger.info("Done")


    def _Init_Socket(self):
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind(self.BIND_ADDRESS)
        self.listen_sock.listen( self.MAX_CONNECTIONS )
        self.logger.info('Listning on %s:%d...' % self.BIND_ADDRESS)


    def _kill_all(self):
        atexit.register(self._kill_all())

        for worker in self.workers:
            os.kill(worker, signal.SIGTERM)

    def _Server_Loop(self):
        self._Init_Socket()

        for i in range(self.NUM_OF_CHILDS):
            pid = os.fork()

            if pid == 0:
                logging.info(f"Starting new fork: {i}")

                while True:
                    conn, addr = self.listen_sock.accept()
                    logging.info(f'Accepted new connection {addr}')

                    try:
                        self._handle(conn)
                    except Exception as e:
                        logging.error(f'error, while proccessing connection: {str(e)}')

                    conn.close()
                    logging.info(f'connection closed {addr}')
            else:
                self.workers.append(pid)

        for worker in self.workers:
            os.waitpid(worker, 0)

