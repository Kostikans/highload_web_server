import asyncio
import logging
import os

from server.server import Server

def main():
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting server")
    my_server = Server()
    my_server.Server_Loop()

if __name__ == '__main__':
    main()
