import socket
import sys
import time
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from logs import client_log_config

log = logging.getLogger('client')


@log_
def create_client_message(action):
    if action == 'presence':
        msg = {"action": action,
               "time": time.time(),
               "user": {"account_name": "Guest"}
               }
        log.info(f'Пользователем "{msg["user"]["account_name"]}" Создано клиентское сообщение типа "{action}".')
        return msg
    elif action == 'message':
        msg_text = input('Input message: ')
        msg = {
            "action": action,
            "time": time.time(),
            "user": {"account_name": "Guest"},
            "text": msg_text
        }
        log.info(f'Пользователем "{msg["user"]["account_name"]}" отправлено сообщение: "{msg_text}"')
        return msg


@log_
def process_answer(answer):
    if "response" in answer:
        if answer["response"] == 200:
            return f'Код - {answer["response"]}. Статус: {answer["status"]}'
        return f'400 : {answer["error"]}'
    elif "action" in answer and answer["action"] == "message":
        sender = answer['sender']
        text = answer['text']
        return f'{sender}: {text}'
    raise ValueError


def main():
    log.info('Процесс соединения с сервером запущен.')
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        client_mode = sys.argv[3]
        if server_port > 65535 or server_port < 1024:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 7777
        client_mode = 'send'
        print(f'Не передан режим работы. Использован режим "{client_mode}"')
        log.warning(f'Параметры не переданы. Использованы параметры по умолчанию - '
                    f'IP: {server_address}; PORT: {server_port}; MODE: {client_mode}')
    except ValueError as val_err:
        log.error(f'Указан недопустимый порт - {server_port}')
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_address, server_port))
        send_message(client_socket, create_client_message('presence'))
        log.info('Сообщение на сервер отправлено.')
        try:
            answer_from_server = process_answer(get_message(client_socket))
            print(answer_from_server)
            log.info(f'Сообщение от сервера - {answer_from_server}')
        except ValueError:
            log.error('Не удалось разобрать сообщение от сервера. Ключ "Response" отсутствует в ответе сервера.')
            sys.exit(1)

        while True:
            if client_mode == 'read':
                try:
                    print(process_answer(get_message(client_socket)))
                except ValueError as err:
                    print('Ошибка при приеме сообщения.')
                    log.error(f'Не удалось разобрать сообщение от сервера. {err}')

            else:
                try:
                    send_message(client_socket, create_client_message('message'))
                except Exception as err:
                    print('Что-то пошло не так. Попробуйте подключиться к серверу еще раз.')
                    log.error(f'Ошибка при попытке отправить сообщение. {err}')


if __name__ == '__main__':
    main()
