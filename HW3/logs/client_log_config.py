import logging


log = logging.getLogger('client')

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

file_handler = logging.FileHandler("logs/client.log", encoding='utf-8')
file_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
