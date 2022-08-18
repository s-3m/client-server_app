import argparse
import socket
import sys
import threading
import time

from PyQt5.QtWidgets import QApplication

from Errors.my_err import ServerError
from client.GUI_main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
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
                    print(f'\nСообщение от {message[0]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]}:\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    log.error('Попытка удаления несуществующего контакта.')
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
                        log.error('Не удалось отправить информацию на сервер.')

    def run(self):
        help_msg = '1 - отправить сообщение\n' \
                   '2 - История сообщений\n' \
                   '3 - Список контактов\n' \
                   '4 - Редактор контактов\n' \
                   '5 - Завершение соединения'
        print(help_msg)
        while True:
            while True:
                command = input('Введите команду: ')
                if command in ('1', '2', '3', '4', '5'):
                    break
                print('Команда указана неверно. Повторите попытку.')

            if command == '1':
                self.create_user_message()
            elif command == '5':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_msg())
                    except Exception as e:
                        print(e)
                    print('Соединение завершено!')
                    log.info('Соединение завершено по инициативе пользователяю')
                    time.sleep(0.5)
                    break
            elif command == '3':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == '4':
                self.edit_contacts()

            elif command == '2':
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
                except OSError as err:
                    if err.errno:
                        log.critical(f'Потеряно соединение с сервером (cr-159).')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError) as err:
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
                            self.database.save_message(message['sender'], self.account_name, message['text'])
                        except Exception as e:
                            print(e)


# @log_
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


if __name__ == '__main__':
    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке, то запросим его
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект.
        # Иначе - выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    # Записываем логи
    log.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Создаём объект базы данных
    database = ClientDB(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()
