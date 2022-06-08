import json
import select
import socket
import sys
import time

from common.utils import send_message, get_message
import logging
from log_decorator import log_
from logs import server_log_config

log = logging.getLogger('server')


@log_
def create_server_message(message, message_list, client_names, client_list, client_sock):
    if "action" in message and message["action"] == "presence" and "time" in message \
            and "user" in message:
        if message['user']['account_name'] not in client_names.keys():
            client_names[message['user']['account_name']] = client_sock
            send_message(client_sock, {"response": 200, "status": "OK"})
        else:
            send_message(client_sock, {'response': 400, 'error': 'Имя пользователя уже занято'})
            client_list.remove(client_sock)
            client_sock.close()
            log.info('Пользователь указал используемое имя')
        return

    elif "action" in message and message["action"] == "message" and "time" in message \
            and "sender" in message and "text" in message:
        message_list.append(message)
        log.info(f'Получено сообщение: "{message["text"]}" от пользователя {message["user"]["account_name"]}')
        return

    else:
        send_message(client_sock, {"response": 400, "error": "Bad Request"})
        return


@log_
def send_to_user(message, client_names, send_data_lst, recv):
    client_socket = client_names[message['destination']]
    print('-'*50)
    print(send_data_lst)
    print(client_socket)
    print('-' * 50)
    if message['destination'] in client_names.keys() and client_socket in send_data_lst:
        send_message(client_socket, message)
    elif message['destination'] in client_names and client_socket not in send_data_lst:
        raise ConnectionError
    else:
        log.error(f'Отправка невозможна. Пользователь с именем {message["destination"]} не зарегистрирован.')


def main():
    # Получаем номер порта из командной строки или назначаем свой.
    # log.info('Старт сервера.')
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = 7777
        if 65535 < listen_port or listen_port < 1024:
            raise ValueError
        # log.info(f'Сервер слушает порт - {listen_port}')
    except IndexError:
        print('Не указан номер порта!')
        log.critical('Не передан параметр номера порта "-p"')
        sys.exit(1)
    except ValueError:
        print('Номер порта должен быть в пределах от 1024 до 65535.')
        log.error(f'Указан недопустимый номер порта - {listen_port}')
        sys.exit(1)

    # Получаем ip-adress из параметров строки или назначаем свой
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
        # log.info(f'Сервер слушает - {listen_address}')
    except IndexError:
        print('После команды "-a" необходимо указать IP-adress')
        log.critical('Не передан параметр IP "-a"')
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((listen_address, listen_port))
        server_socket.settimeout(1)
        server_socket.listen()

        client_list = []
        messages = []
        client_names = dict()

        while True:
            try:
                client_socket, address = server_socket.accept()
            except OSError:
                pass
                    # print(f'I`am listen...IP: {listen_address} on {listen_port} port')
            else:
                client_list.append(client_socket)
                log.info(f'установлено соединение с {address}')

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if client_list:
                    recv_data_lst, send_data_lst, err_lst = select.select(client_list, client_list, err_lst, 0)
            except OSError:
                pass

            if recv_data_lst:
                for i in recv_data_lst:
                    try:
                        create_server_message(get_message(i), messages, client_names, client_list, i)
                    except:
                        log.info(f'Потеряно соединение с клиентом {i.getpeername()}')
                        client_list.remove(i)

            for i in messages:
                try:
                    send_to_user(i, client_names, send_data_lst)
                except Exception:
                    log.info(f'Не удалось отправить сообщение. Связь с клиентом {i["destination"]} была потеряна.')
                    client_list.remove(client_names[i['destination']])
                    del client_names[i['destination']]
            messages.clear()


if __name__ == '__main__':
    main()
