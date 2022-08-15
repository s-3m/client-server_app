import argparse
import socket
import sys
import threading
import time

from Errors.my_err import ServerError
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from common.meta_classes import ClientVerifier
from database.clients_db import ClientDB

log = logging.getLogger('client')
sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        super().__init__()
        self.account_name = account_name
        self.sock = sock
        self.database = database

    @log_
    def create_user_message(self):
        to_user = input('Введите получателя: ')
        msg_text = input('Введите текст: ')

        with database_lock:
            if not self.database.check_user(to_user):
                log.error(f'Попытка отправить сообщение '
                             f'незарегистрированому получателю: {to_user}')
                return
        msg = {
            'action': 'message',
            'time': time.time(),
            'sender': self.account_name,
            'destination': to_user,
            'text': msg_text
        }
        log.info(f'Создан словарь сообщения - {msg}')

        with database_lock:
            self.database.save_message(self.account_name, to_user, msg_text)

        with sock_lock:
            try:
                send_message(self.sock, msg)
                log.info(f'Сообщение отправлено пользователю {to_user}')
            except OSError as err:
                if err.errno:
                    log.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    log.error('Не удалось передать сообщение. Таймаут соединения')

    def create_exit_msg(self):
        return {
            'action': 'exit',
            'time': time.time(),
            'account_name': self.account_name
        }

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')

    def run(self):
        help_msg = '1 - отправить сообщение\n2 - список команд\n3 - завершить соединение\n4 - Список контактов\n5 - Редактор контактов\n6 - История сообщений'
        print(help_msg)
        while True:
            while True:
                command = input('Введите команду: ')
                if command in ('1', '2', '3', '4', '5', '6'):
                    break
                print('Команда указана неверно. Повторите попытку.')

            if command == '1':
                self.create_user_message()
            elif command == '2':
                print(help_msg)
            elif command == '3':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_msg())
                    except Exception as e:
                        print(e)
                    print('Соединение завершено!')
                    log.info('Соединение завершено по инициативе пользователяю')
                    time.sleep(0.5)
                    break
            elif command == '4':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == '5':
                self.edit_contacts()

            elif command == '6':
                self.print_history()


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        super().__init__()
        self.account_name = account_name
        self.sock = sock
        self.database = database

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError) as err:
                    log.critical(f'Потеряно соединение с сервером - {err}')
                    break
                except (Exception, BaseException) as err:
                    log.error(f'Не удалось распознать полученное сообщение - {err}')
                else:
                    if 'action' in message and message['action'] == 'message' and 'sender' in message and \
                            'text' in message and message['destination'] == self.account_name:
                        print(f'\n{message["sender"]}: {message["text"]}')
                    log.info(f'Получено сообщение от пользователя {message["sender"]}')
                    with database_lock:
                        try:
                            self.database.save_message(message['sender'], self.account_name, message['message_taxt'])
                        except Exception as e:
                            print(e)


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


def add_contact(sock, username, contact):
    log.debug(f'Создание контакта {contact}')
    msg = {
        'action': 'add_contact',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_message(sock, msg)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


def remove_contact(sock, username, contact):
    log.debug(f'Создание контакта {contact}')
    msg = {
        'action': 'remove_contact',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_message(sock, msg)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления контакта')
    print('Ошибка удаление контакта.')


def contacts_list_request(sock, name):
    log.debug(f'запрос списка контактов пользователя {name}')
    msg = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': name
    }
    send_message(sock, msg)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['answer_list']
    else:
        raise ServerError('Неудалось получить список контактов')


def user_list_request(sock, username):
    log.debug(f'Запрос списка пользователей {username}')
    msg = {
        'action': 'users_request',
        'time': time.time(),
        'account_name': username
    }
    send_message(sock, msg)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['answer_list']
    else:
        raise ServerError('Не удалось получить список пользователей')


def db_load(sock, db, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        log.error('Ошибка запроса списка пользователей')
        print('error - line145')
    else:
        db.add_users(users_list)

    try:
        contact_list = contacts_list_request(sock, username)
    except ServerError:
        log.error('Ошибка запроса списка контактов')
    else:
        for contact in contact_list:
            db.add_contact(contact)


def main():
    log.info('Клиентский модуль. Процесс соединения с сервером запущен.')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Пожалуйста введите имя пользователя: ')
    else:
        print(f'Здравствуйте {client_name}. Добро пожаловать')

    log.info(f'Соединение запущено клиентом {client_name}. IP: {server_address}; PORT: {server_port}')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.settimeout(1)
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
            client_db = ClientDB(client_name)
            db_load(client_socket, client_db, client_name)

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
