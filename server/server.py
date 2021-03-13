import select
import os
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
        self.NUM_OF_CHILDS = 4
        self.BACK_LOG = 10

        self.childrens_pull = []
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def Run(self):
        self._Init_Forked_Procceses()
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
            self._send_response(sock,response)
            return

        if not request.OK:
            logging.info('Done with error')
            self._send_response(sock, HttpResponseBadResponse())
            return

        if config.MEDIA_ROOT not in request.PATH.parents:
            print(config.MEDIA_ROOT)
            print(request.PATH.parents)
            response = HttpResponseForbidden()
            self._send_response(sock,response)
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

    def _create_child(self):
        child_pipe, parent_pipe = socket.socketpair()
        pid = os.fork()
        if pid == 0:
            child_pipe.close()
            try:
                while 1:
                    command = parent_pipe.recv(1)
                    self.logger.info('Child get command=%s' % repr(command))

                    connection, (client_ip, client_port) = self.listen_sock.accept()
                    self.logger.info('Accept connection %s:%d' % (client_ip, client_port))
                    self.logger.info('Child send "begin"')
                    parent_pipe.send(b'B')

                    self._handle(connection)

                    connection.close()

                    self.logger.info('Child send "free"')
                    parent_pipe.send(b'F')

            except KeyboardInterrupt:
                sys.exit()

        self.logger.info('Starting child with PID: %s' % pid)
        self.childrens_pull.append(ChildController(child_pipe))

        parent_pipe.close()
        return child_pipe

    def _Init_Forked_Procceses(self):
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind(self.BIND_ADDRESS)
        self.listen_sock.listen(self.BACK_LOG)
        self.listen_sock.setblocking(False)
        self.logger.info('Listning on %s:%d...' % self.BIND_ADDRESS)
        for i in range(self.NUM_OF_CHILDS):
            self._create_child()

    def _Server_Loop(self):
        to_read = [self.listen_sock] + [c.pipe.fileno() for c in self.childrens_pull]
        while True:

            readables, writables, exceptions = select.select(to_read, [], [])
            if self.listen_sock in readables:
                self.logger.info('Listning socket is readable')

                for c in self.childrens_pull:
                    if c.is_free:
                        self.logger.info('Send command "accept connection" to child')
                        c.pipe.send(b'A')
                        command = c.pipe.recv(1)
                        self.logger.info(
                            'Parent get command %s from child. Mark free.' %
                            repr(command))
                        c.is_free = False
                        break
                    else:
                        self.logger.info('Child not free')
                else:
                    raise Exception('No more childrens.')

            for c in self.childrens_pull:
                if c.pipe.fileno() in readables:
                    command = c.pipe.recv(1)
                    if command != b'F':
                        raise Exception(repr(command))
                    self.logger.info(
                        'Parent get command %s from child. Mark free.' %
                        repr(command))
                    c.is_free = True
