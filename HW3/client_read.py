import argparse
import json
import socket
import sys
import threading
import time
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from logs import client_log_config

log = logging.getLogger('client')


class ClientSender(threading.Thread):
    def __init__(self, account_name, sock):
        super().__init__()
        self.account_name = account_name
        self.sock = sock

    @log_
    def create_user_message(self):
        to_user = input('Введите получателя: ')
        msg_text = input('Введите текст: ')
        msg = {
            'action': 'message',
            'time': time.time(),
            'sender': self.account_name,
            'destination': to_user,
            'text': msg_text
        }
        log.info(f'Создан словарь сообщения - {msg}')

        try:
            send_message(self.sock, msg)
            log.info(f'Сообщение отправлено пользователю {to_user}')
        except Exception as err:
            print(err)
            log.critical('Соединение с сервером потеряно')
            sys.exit(1)

    def create_exit_msg(self):
        return {
            'action': 'exit',
            'time': time.time(),
            'account_name': self.account_name
        }

    def run(self):
        help_msg = '1 - отправить сообщение\n2 - список команд\n3 - завершить соединение'
        print(help_msg)
        while True:
            while True:
                command = input('Введите команду: ')
                if command in ('1', '2', '3'):
                    break
                print('Команда указана неверно. Повторите попытку.')

            if command == '1':
                self.create_user_message()
            elif command == '2':
                print(help_msg)
            else:
                try:
                    send_message(self.sock, self.create_exit_msg())
                except:
                    pass
                print('Соединение завершено')
                log.info('Пользователь завершил соединение')
                break


class ClientReader(threading.Thread):
    def __init__(self, account_name, sock):
        super().__init__()
        self.account_name = account_name
        self.sock = sock

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if 'action' in message and message['action'] == 'message' and 'sender' in message and \
                        'text' in message and message['destination'] == self.account_name:
                    print(f'\n{message["sender"]}: {message["text"]}')
                    log.info(f'Получено сообщение от пользователя {message["sender"]}')
                elif 'response' in message and 'error' in message:
                    print(f'\n{message["error"]}')
                else:
                    log.error(f'Формат полученного сообщения некорректный - {message}')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError) as err:
                log.critical(f'Потеряно соединение с сервером - {err}')
                break
            except (Exception, BaseException) as err:
                log.error(f'Не удалось распознать полученное сообщение - {err}')


@log_
def create_presence_message(my_name):
    msg = {"action": 'presence',
           "time": time.time(),
           "user": {"account_name": my_name}
           }
    log.info(f'Пользователем "{msg["user"]["account_name"]}" Создано клиентское сообщение типа "presence".')
    return msg


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
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        log.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name


def main():
    log.info('Клиентский модуль. Процесс соединения с сервером запущен.')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Пожалуйста введите имя пользователя: ')
    else:
        print(f'Здравствуйте {client_name}. Добро пожаловать')

    log.info(f'Соединение запущено клиентом {client_name}. IP: {server_address}; PORT: {server_port}')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_address, server_port))
        send_message(client_socket, create_presence_message(client_name))
        log.info('Приветственное сообщение на сервер отправлено.')
        try:
            answer_from_server = answer_to_connect(get_message(client_socket))
            print(answer_from_server)
            log.info(f'Сообщение от сервера - {answer_from_server}')
        except ValueError:
            log.error('Не удалось разобрать сообщение от сервера. Ключ "Response" отсутствует в ответе сервера.')
            sys.exit(1)
        except (ConnectionRefusedError, ConnectionError):
            log.critical(
                f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                f'конечный компьютер отверг запрос на подключение.')
            exit(1)

        else:
            module_receiver = ClientReader(client_name, client_socket)
            module_receiver.daemon = True
            module_receiver.start()

            module_sender = ClientSender(client_name, client_socket)
            module_sender.daemon = True
            module_sender.start()
            log.info('Процессы на чтение и отправку сообщений запущены')

            while True:
                time.sleep(1)
                if module_receiver.is_alive() and module_sender.is_alive():
                    continue
                break


if __name__ == '__main__':
    main()
