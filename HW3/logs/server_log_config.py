import logging.handlers
import logging

log = logging.getLogger('server')

format = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

file_handler = logging.handlers.TimedRotatingFileHandler('logs/server.log', encoding='utf-8', when='D', interval=1)
file_handler.setFormatter(format)

log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
