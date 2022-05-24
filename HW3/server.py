import json
import socket
import sys
from common.utils import send_message, get_message


def create_server_message(message):
    if "action" in message and message["action"] == "presence" and "time" in message \
            and "user" in message and message["user"]["account_name"] != '':
        return {"response": 200, "status": "OK"}
    return {"response": 400, "error": "Bad Request"}


def main():
    # Получаем номер порта из командной строки или назначаем свой.
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = 7777
        if 65535 < listen_port or listen_port < 1024:
            raise ValueError
    except IndexError:
        print('Не указан номер порта!')
        sys.exit(1)
    except ValueError:
        print('Номер порта должен быть в пределах от 1024 до 65535.')
        sys.exit(1)

    # Получаем ip-adress из параметров строки или назначаем свой
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        print('После команды "-a" необходимо указать IP-adress')
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((listen_address, listen_port))
        server_socket.listen()

        while True:
            print(f'I`am listen...IP: {listen_address} on {listen_port} port')
            client_socket, address = server_socket.accept()
            try:
                message_from_client = get_message(client_socket)
                print(message_from_client)
                response = create_server_message(message_from_client)
                send_message(client_socket, response)
            except(ValueError, json.JSONDecodeError):
                print('Ошибка! Неправильный формат сообщеня.')


if __name__ == '__main__':
    main()
