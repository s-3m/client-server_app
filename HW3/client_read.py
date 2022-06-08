import socket
import sys
import threading
import time
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from logs import client_log_config

log = logging.getLogger('client')


@log_
def create_presence_message(my_name):
        msg = {"action": 'presence',
               "time": time.time(),
               "user": {"account_name": my_name}
               }
        log.info(f'Пользователем "{msg["user"]["account_name"]}" Создано клиентское сообщение типа "presence".')
        return msg


@log_
def create_user_message(socket, my_name):
    help_msg = '1 - отправить сообщение\n2 - список команд\n3 - завершить соединение'
    print(help_msg)
    while True:
        while True:
            command = input('Введите команду: ')
            if command in ('1', '2', '3'):
                break
            print('Команда указана неверно. Повторите попытку.')

        if command == '1':
            to_user = input('Введите получателя: ')
            msg_text = input('Введите текст: ')
            msg = {
                'action': 'message',
                'time': time.time(),
                'sender': my_name,
                'destination': to_user,
                'text': msg_text
            }
            log.info(f'Создан словарь сообщения - {msg}')

            try:
                send_message(socket, msg)
                log.info(f'Сообщение отправлено пользователю {to_user}')
            except Exception as err:
                print(err)
                log.critical('Соединение с сервером потеряно')
                sys.exit(1)

        elif command == '2':
            print(help_msg)
        else:
            print('Соединение завершено')
            log.info('Пользователь завершил соединение')
            break


@log_
def answer_to_connect(answer):
    if "response" in answer:
        if answer["response"] == 200:
            return f'Код - {answer["response"]}. Статус: {answer["status"]}'
        return f'400 : {answer["error"]}'
    elif "action" in answer and answer["action"] == "message":
        sender = answer['sender']
        text = answer['text']
        return f'{sender}: {text}'
    raise ValueError


@log_
def get_message_from_user(socket, my_name):
    while True:
        try:
            message = get_message(socket)
            if 'action' in message and message['action'] == 'message' and 'sender' in message and \
                    'text' in message and message['destination'] == my_name:
                print(f'\n{message["sender"]}: {message["text"]}')
                log.info(f'Получено сообщение от пользователя {message["sender"]}')
            else:
                log.error(f'Формат полученного сообщения некорректный - {message}')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError) as err:
            log.critical(f'Потеряно соединение с сервером - {err}')
            break
        except (Exception, BaseException) as err:
            log.error(f'Не удалось распознать полученное сообщение - {err}')


def main():
    log.info('Процесс соединения с сервером запущен.')
    my_name = ''
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        my_name = sys.argv[3]
        if server_port > 65535 or server_port < 1024:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 7777
        if not my_name:
            while True:
                my_name = input('Пожалуйста, введите ваше имя пользователя: ')
                if my_name.strip() != '':
                    break
                else:
                    print(f'Поле не должно быть пустым')
        log.warning(f'Параметры не переданы. Использованы параметры по умолчанию - '
                    f'IP: {server_address}; PORT: {server_port}')
    except ValueError:
        log.error(f'Указан недопустимый порт - {server_port}')
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_address, server_port))
        send_message(client_socket, create_presence_message(my_name))
        log.info('Сообщение на сервер отправлено.')
        try:
            answer_from_server = answer_to_connect(get_message(client_socket))
            print(answer_from_server)
            log.info(f'Сообщение от сервера - {answer_from_server}')
        except ValueError:
            log.error('Не удалось разобрать сообщение от сервера. Ключ "Response" отсутствует в ответе сервера.')
            sys.exit(1)

        else:
            read_thread = threading.Thread(target=get_message_from_user, args=(client_socket, my_name))
            read_thread.daemon = True
            read_thread.start()

            send_thread = threading.Thread(target=create_user_message, args=(client_socket, my_name))
            send_thread.daemon = True
            send_thread.start()
            log.info('Процессы на чтение и отправку сообщений запущены')

            while True:
                time.sleep(1)
                if read_thread.is_alive() and send_thread.is_alive():
                    continue
                break


if __name__ == '__main__':
    main()
