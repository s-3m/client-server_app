import logging
import sys
import traceback

from logs import client_log_config, server_log_config


def log_(func):
    def wrapper(*args, **kwargs):
        side = 'server' if 'server.py' in sys.argv[0] else 'client'
        log = logging.getLogger(side)
        log.info(f'Обращение к функции {func.__name__} с аргументами: {args}, {kwargs} ||| '
                 f'Вызывающая функия - "{traceback.format_stack()[0].strip().split()[-1]}"')
        result = func(*args, **kwargs)
        return result

    return wrapper
