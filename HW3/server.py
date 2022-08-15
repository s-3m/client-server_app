import argparse
import configparser
import os.path
import select
import socket
import sys
from time import sleep

from common.meta_classes import ServerVerifier
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from common.descriptors import ServerPortChecker
from database.server_db import ServerDB
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_GUI import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

log = logging.getLogger('server')
# флаг о подключении нового пользователя
new_connection = False
conflag_lock = threading.Lock()


@log_
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    port = ServerPortChecker()

    def __init__(self, listen_address, listen_port, server_db):
        super().__init__()
        self.sock = None
        self.server_db = server_db
        self.addr = listen_address
        self.port = listen_port

        self.clients = []
        self.messages = []
        self.names = dict()

    def init_socket(self):
        log.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.addr}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.addr, self.port))
        server_socket.settimeout(0.5)

        self.sock = server_socket
        self.sock.listen()
        print('Сервер запущен!')

    def run(self):
        self.init_socket()

        while True:
            try:
                client_socket, address = self.sock.accept()
            except OSError:
                pass
            else:
                self.clients.append(client_socket)
                log.info(f'установлено соединение с {address}')

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, err_lst, 0)
            except OSError as err:
                log.error(f'Ошибка работы с сокетами: {err}')

            if recv_data_lst:
                for i in recv_data_lst:
                    try:
                        self.create_server_message(get_message(i), i)
                    except(Exception) as err:
                        print(err)
                        log.info(f'Потеряно соединение с клиентом {i.getpeername()}')
                        for name in self.names:
                            if self.names[name] == i:
                                self.server_db.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(i)

            for message in self.messages:
                try:
                    self.send_to_user(message, send_data_lst)
                except KeyError:
                    log.warning(f'Пользователь указал не зарегистрированного пользователя "{message["destination"]}"')
                    self.create_server_message(message, None)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    log.info(
                        f'Не удалось отправить сообщение. Связь с клиентом {message["destination"]} была потеряна.')
                    self.clients.remove(self.names[message['destination']])
                    self.server_db.user_logout(message['destination'])
                    del self.names[message['destination']]
            self.messages.clear()

    @log_
    def send_to_user(self, message, send_data_lst):
        if message['destination'] in self.names and self.names[message['destination']] in send_data_lst:
            send_message(self.names[message['destination']], message)
        elif message['destination'] in self.names and self.names[message['destination']] not in send_data_lst:
            raise ConnectionError
        else:
            log.error(f'Отправка невозможна. Пользователь с именем {message["destination"]} не зарегистрирован.')

    @log_
    def create_server_message(self, message, client):
        global new_connection

        if "action" in message and message["action"] == "presence" and "time" in message \
                and "user" in message:
            if message['user']['account_name'] not in self.names.keys():
                self.names[message['user']['account_name']] = client
                client_ip, client_port = client.getpeername()
                self.server_db.user_login(message['user']['account_name'], client_ip, client_port)
                send_message(client, {"response": 200, "status": "OK"})
                with conflag_lock:
                    new_connection = True
            else:
                send_message(client, {'response': 400, 'error': 'Имя пользователя уже занято'})
                self.clients.remove(client)
                client.close()
                log.info('Пользователь указал используемое имя')
            return

        elif "action" in message and message["action"] == "message" and "time" in message \
                and "sender" in message and "text" in message and message['destination'] not in self.names:
            client_sock = self.names[message['sender']]
            send_message(client_sock, {"response": 400, "error": "Такой пользователь не зарегистрирован"})
            return

        elif "action" in message and message["action"] == "message" and "time" in message \
                and "sender" in message and "text" in message and self.names[message['destination']] in self.clients:
            self.messages.append(message)
            log.info(f'Получено сообщение: "{message["text"]}" от пользователя {message["sender"]}')
            self.server_db.process_message(message['sender'], message['destination'])
            return
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
            self.server_db.user_logout(message['account_name'])
            self.clients.remove(self.names[message['account_name']])
            self.names[message['account_name']].close()
            del self.names[message['account_name']]
            with conflag_lock:
                new_connection = True
            return

        elif 'action' in message and message['action'] == 'get_contacts' and 'user' in message and \
                self.names[message['user']] == client:
            response = {'response': 202}
            response['answer_list'] = self.server_db.get_contacts(message['user'])
            send_message(client, response)

        elif 'action' in message and message[
            'action'] == 'add_contact' and 'account_name' in message and 'user' in message \
                and self.names[message['user']] == client:
            self.server_db.add_contact(message['user'], message['account_name'])
            send_message(client, {'response': 200})

        elif 'action' in message and message[
            'action'] == 'remove_contact' and 'account_name' in message and 'user' in message \
                and self.names[message['user']] == client:
            self.server_db.remove_contact(message['user'], message['account_name'])
            send_message(client, {'response': 200})

        elif 'action' in message and message['action'] == 'users_request' and 'account_name' in message \
                and self.names[message['account_name']] == client:
            response = {'response': 202}
            response['answer_list'] = [user[0] for user in self.server_db.users_list()]
            send_message(client, response)


        else:
            send_message(client, {"response": 400, "error": "Bad Request"})
            return


def print_help():
    sleep(0.1)
    print('-----------------------------------------------------------')
    print('all - список всех зарегестрированных пользователей')
    print('active - список активных пользователей')
    print('login history - просмотр истории входа')
    print('help - список доступных команд')
    print('-----------------------------------------------------------')


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address']
    )

    server_db = ServerDB(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file'])
    )

    server = Server(listen_address, listen_port, server_db)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(server_db))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(server_db))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(server_db))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_btn.triggered.connect(list_update)
    main_window.show_history_btn.triggered.connect(show_statistics)
    main_window.server_settings.triggered.connect(server_config)

    server_app.exec_()

    # print_help()

    # while True:
    #     answer = input('Введите команду: ')
    #     if answer == 'all':
    #         for user in sorted(server_db.user_list()):
    #             print(f'Пользователь "{user[0]}". Дата последнего входа - {user[1]}')
    #     elif answer == 'active':
    #         for user in sorted(server_db.active_users_list()):
    #             print(f'Пользователь "{user[0]}". IP: {user[1]}; Port: {user[2]}; Дата последнего входа - {user[3]}')
    #     elif answer == 'login history':
    #         need_user = input('Введите имя пользователя либо оставьте поле пустым: ')
    #         if need_user:
    #             for user in server_db.login_history(need_user):
    #                 print(
    #                     f'Пользователь "{user[0]}". IP: {user[2]}; Port: {user[3]}; Дата последнего входа - {user[1]}')
    #         else:
    #             for user in server_db.login_history():
    #                 print(
    #                     f'Пользователь "{user[0]}". IP: {user[2]}; Port: {user[3]}; Дата последнего входа - {user[1]}')
    #     elif answer == 'help':
    #         print_help()
    #     else:
    #         print('Неверная команда!')


if __name__ == '__main__':
    main()
