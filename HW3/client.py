import socket
import sys
import time
from common.utils import send_message, get_message
import logging
from logs import client_log_config

log = logging.getLogger('client')

def create_client_message(action, msg_text=None):
    msg = {"action": action,
           "time": time.time(),
           "user": {"account_name": "Guest"}
           }
    return msg


def process_answer(answer):
    if "response" in answer:
        if answer["response"] == 200:
            return f'Cоединение с сервером установлено. ' \
                   f'Код - {answer["response"]}. Статус: {answer["status"]}'
        return f'400 : {answer["error"]}'
    raise ValueError


def main():
    log.debug('Процесс запущен')
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port > 65535 or server_port < 1024:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 7777
    except ValueError:
        print('Порт должен быть в диапазоне от 1024 до 65535.')
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_address, server_port))
        send_message(client_socket, create_client_message('presence'))
        try:
            answer_from_server = process_answer(get_message(client_socket))
            print(answer_from_server)
        except ValueError:
            print('Не удалось разобрать сообщение от сервера')


if __name__ == '__main__':
    main()
