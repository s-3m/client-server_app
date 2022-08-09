import argparse
import select
import socket
import sys
from common.meta_classes import ServerVerifier
from common.utils import send_message, get_message
import logging
from log_decorator import log_
from common.descriptors import ServerPortChecker

log = logging.getLogger('server')


@log_
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(metaclass=ServerVerifier):
    port = ServerPortChecker()

    def __init__(self, listen_address, listen_port):
        self.sock = None
        self.addr = listen_address
        self.port = listen_port
        print(self.port)

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

    def main_loop(self):
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
            except OSError:
                pass

            if recv_data_lst:
                for i in recv_data_lst:
                    try:
                        self.create_server_message(get_message(i), i)
                    except:
                        log.info(f'Потеряно соединение с клиентом {i.getpeername()}')
                        self.clients.remove(i)

            for message in self.messages:
                try:
                    self.send_to_user(message, send_data_lst)
                except KeyError:
                    log.warning(f'Пользователь указал не зарегистрированного пользователя "{message["destination"]}"')
                    self.create_server_message(message, None)
                except Exception:
                    log.info(
                        f'Не удалось отправить сообщение. Связь с клиентом {message["destination"]} была потеряна.')
                    self.clients.remove(self.names[message['destination']])
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
        if "action" in message and message["action"] == "presence" and "time" in message \
                and "user" in message:
            if message['user']['account_name'] not in self.names.keys():
                self.names[message['user']['account_name']] = client
                send_message(client, {"response": 200, "status": "OK"})
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
            return
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
            self.clients.remove(self.names['account_name'])
            self.names['account_name'].close()
            del self.names['account_name']
            return

        else:
            send_message(client, {"response": 400, "error": "Bad Request"})
            return


def main():
    listen_address, listen_port = arg_parser()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
