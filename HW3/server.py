import argparse
import configparser
import os.path
import select
import socket
import sys
from time import sleep

from PyQt5 import Qt

from HW3.common.variables import DEFAULT_PORT
from common.meta_classes import ServerVerifier
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from common.descriptors import ServerPortChecker
from database.server_db import ServerDB
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server.main_window import MainWindow
from server.core import MessageProcessor
from PyQt5.QtGui import QStandardItemModel, QStandardItem

log = logging.getLogger('server')
# флаг о подключении нового пользователя
new_connection = False
conflag_lock = threading.Lock()


@log_
def arg_parser(default_port, default_address):
    log.debug(
        f'Инициализация парсера аргументов коммандной строки: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    log.debug('Аргументы успешно загружены.')
    return listen_address, listen_port, gui_flag


def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    config = config_load()
    listen_address, listen_port, gui_flag = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address']
    )

    server_db = ServerDB(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file'])
    )

    server = MessageProcessor(listen_address, listen_port, server_db)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завершаем основной цикл сервера.
                server.running = False
                server.join()
                break
    else:
        server_app = QApplication(sys.argv)
        # server_app.setAttribute(Qt.)
        main_window = MainWindow(server_db, server, config)

        server_app.exec_()
        server.running = False


if __name__ == '__main__':
    main()
