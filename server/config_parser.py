import logging


logger = logging.getLogger('main')

def parse_config(filename) -> dict:
    config = {}
    with open(filename) as fp:
        line = fp.readline()
        while line:
            parsed_line = line.split()
            config[parsed_line[0]] = parsed_line[1]
            line = fp.readline()
    logger.info("Config parsed")
    return config