import logging
import os
from urllib.parse import unquote

import config


class HttpRequest:
    def __init__(self, raw_request: str):

        self.raw_request = raw_request
        self.OK = False
        self.METHOD = None
        self.URL = None
        self.HTTP_VERSION = None
        self.PATH = None
        self.REALPATH = None
        self.HEADERS = {}

        try:
            self.__parse_headers()
            self.__parse_url()

        except Exception as e:
            logging.info(f"Error while request parsing: {str(e)}")
            return

    def __parse_headers(self):
        headers_list = self.raw_request.split("\r\n")

        if len(headers_list) == 0:
            logging.info("length is zero")
            return

        self.METHOD, self.URL, self.HTTP_VERSION = headers_list[0].split()

        self.METHOD = self.METHOD.upper()

        for header in headers_list[1:]:
            header_name_value = header.split(": ")
            if len(header_name_value) != 2:
                continue

            header_name, header_value = header.split(": ")

            self.HEADERS[header_name] = header_value

            self.OK = True

    def __parse_url(self):
        if self.URL is not None:
            self.URL = unquote(self.URL.split("?")[0])
            self.PATH = config.PROJECT_ROOT.joinpath(self.URL[1:])
            self.REALPATH = self.URL[1:]

    def __str__(self):
        return self.raw_request

