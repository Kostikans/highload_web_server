import atexit
import select
import os
import signal
import sys
import socket
import logging
import asyncio
import multiprocessing
import random
import logging

import config

from server.request.request import HttpRequest
from server.response.response import HttpResponseMethodNotAllowed, BaseHttpResponse, HttpResponseForbidden, \
    HttpResponseNotFound, HttpResponseOK, HttpResponseBadResponse


class Server:
    def __init__(self):

        self.BIND_ADDRESS = ('localhost', config.PORT)
        self.NUM_OF_CHILDS = config.CPU_LIMIT
        self.workers = []
        self.listen_sock = None
        atexit.register(self._kill)

    def _process_request(self, buffer: bytes) -> HttpRequest:
        raw_request = buffer.decode()
        request = HttpRequest(raw_request=raw_request)

        return request

    def _kill(self):
        for w in self.workers:
            w.terminate()
            w.join()

    async def _handle(self, sock):
        in_buffer = ""
        while True:
            part = (await asyncio.get_event_loop().sock_recv(sock, 1024)).decode()
            in_buffer += part
            if '\r\n' in in_buffer or len(part) == 0:
                break

        request = self._process_request(in_buffer.encode())

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

        if str(request.PATH)[len(str(request.PATH)) - 1] != request.REALPATH[
            len(request.REALPATH) - 1] and not os.path.isdir(request.PATH):
            self._send_response(sock, HttpResponseNotFound())
            return

        if os.path.isdir(request.PATH):
            request.PATH = str(request.PATH) + "/index.html"
            if not os.path.isfile(request.PATH):
                self._send_response(sock, HttpResponseForbidden())
                return

        try:
            content = await self._read_file(request.PATH)
        except Exception as e:
            logging.error(str(e))
            self._send_response(sock, HttpResponseNotFound())
            return

        response = HttpResponseOK(content, filename=request.PATH, with_body=request.METHOD != "HEAD")
        await asyncio.get_event_loop().sock_sendall(sock, response.encode())

    async def _read_file(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            content = f.read()
        return content

    def _send_response(self, sock, response: BaseHttpResponse):
        sock.sendall(response.encode())

    def _Init_Socket(self):
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind(self.BIND_ADDRESS)
        self.listen_sock.listen(config.MAX_CONNECTIONS)
        self.listen_sock.setblocking(False)

        logging.info('Listning on %s:%d...' % self.BIND_ADDRESS)

    def Server_Loop(self):
        self._Init_Socket()

        for i in range(self.NUM_OF_CHILDS):
            p = multiprocessing.Process(target=self.worker, args=(self.listen_sock,))
            p.start()
            self.workers.append(p)

        try:
            for worker in self.workers:
                worker.join()
        except KeyboardInterrupt:
            for worker in self.workers:
                worker.terminate()

            self.listen_sock.close()

    def worker(self, sock: socket.socket):
        asyncio.run(self._work(sock))

    async def _work(self, sock: socket.socket):

        while True:

            conn, _ = await asyncio.get_event_loop().sock_accept(sock)

            try:
                await self._handle(conn)
            except Exception as e:
                logging.error(f'error, while proccessing connection: {str(e)}')

            conn.close()
