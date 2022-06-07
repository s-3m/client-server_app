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
def create_server_message(message, message_list, client_names, client):
    if "action" in message and message["action"] == "presence" and "time" in message \
            and "user" in message and message["user"]["account_name"] != '':
        send_message(client, {"response": 200, "status": "OK"})
        return

    elif "action" in message and message["action"] == "message" and "time" in message \
            and "sender" in message and "text" in message:
        message_list.append((message['sender'], message['text']))
        client_names['name'] = message['sender']
        client_names['socket'] = client

        log.info(f'Получено сообщение: "{message["text"]}" от пользователя {message["user"]["account_name"]}')
        return

    else:
        send_message(client, {"response": 400, "error": "Bad Request"})
        return


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
        client_names = {}

        while True:
            # log.info(f'Server listens...IP: {listen_address} on {listen_port} port')
            try:
                client_socket, address = server_socket.accept()
            except OSError as error:
                if error.errno == None:
                    print(f'I`am listen...IP: {listen_address} on {listen_port} port')
                pass
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
                        create_server_message(get_message(i), messages, client_names, i)
                    except:
                        log.info(f'Потеряно соединение с клиентом {i.getpeername()}')
                        client_list.remove(i)

            if messages and send_data_lst:
                message = {
                    'action': 'message',
                    'sender': messages[0][0],
                    'time': time.time(),
                    'text': messages[0][1]
                }
                del messages[0]

                for i in send_data_lst:
                    try:
                        send_message(i, message)
                    except:
                        log.info(f'Потеряно соединение с клиентом {i.getpeername()}')
                        i.close()
                        client_list.remove(i)

            # try:
            #     message_from_client = get_message(client_socket)
            #     log.info(f'Получено сообщение "{message_from_client["action"]}" '
            #              f'от {message_from_client["user"]["account_name"]}')
            #     response = create_server_message(message_from_client)
            #     log.info(f'Сформирован ответ. Статус - {response["response"]}')
            #     send_message(client_socket, response)
            #     log.info('Сообщение успешно отправлено клиенту')
            # except(ValueError, json.JSONDecodeError):
            #     print('Ошибка! Неправильный формат сообщеня.')
            #     log.critical('Ошибка! Неправильный формат сообщеня.')
            #     sys.exit(1)


if __name__ == '__main__':
    main()
