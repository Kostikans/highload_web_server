import asyncio
import logging
import os

from server.server import Server

logger = logging.getLogger('main')


def main():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(process)s] %(message)s',
        '%H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('Run')
    my_server = Server()
    asyncio.run(my_server.Server_Loop())

if __name__ == '__main__':
    main()
