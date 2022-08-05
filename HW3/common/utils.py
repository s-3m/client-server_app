import json
import sys
sys.path.append('../')
from log_decorator import log_


@log_
def send_message(client_socket, message):
    if not isinstance(message, dict):
        raise ValueError
    json_message = json.dumps(message)
    encoding_message = json_message.encode('utf-8')
    client_socket.send(encoding_message)


@log_
def get_message(client_socket):
    encoding_response = client_socket.recv(4096)
    if isinstance(encoding_response, bytes):
        json_response = encoding_response.decode('utf-8')
        if isinstance(json_response, str):
            response = json.loads(json_response)
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError
    raise ValueError
