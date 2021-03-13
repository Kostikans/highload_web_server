import logging


def parse_config(filename) -> dict:
    config = {}
    with open(filename) as fp:
        line = fp.readline()
        while line:
            line = fp.readline()
            parsed_line = line.split()
            config[parsed_line[0]] = parsed_line[1]
    logging.info("Config parsed")
    return config