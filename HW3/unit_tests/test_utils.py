import json
import sys
import unittest
from unittest import TestCase
sys.path.append('..')
from common.utils import send_message, get_message


class SocketEmulation:

    def __init__(self, test_odj):
        self.test_obj = test_odj
        self.encod_message = None
        self.received_message = None

    def send(self, message):
        json_message = json.dumps(self.test_obj)
        self.encod_message = json_message.encode('utf-8')
        self.received_message = message

    def recv(self, _):
        json_test_msg = json.dumps(self.test_obj)
        return json_test_msg.encode('utf-8')


class WrongRecvSocketEmulation(SocketEmulation):
    def recv(self, _):
        return json.dumps(self.test_obj)


class TestUtils(TestCase):
    msg_dict = {
        "action": "presence",
        "time": 1.1,
        "user": {"account_name": "Guest"}
    }
    test_answer_ok = {"response": 200}
    test_answer_error = {"response": 400, "error": "Bad Request"}

    def test_send_message_ok(self):
        socket = SocketEmulation(self.msg_dict)
        send_message(socket, self.msg_dict)
        self.assertEqual(socket.encod_message, socket.received_message)

    def test_send_message_raises(self):
        socket = SocketEmulation(self.msg_dict)
        send_message(socket, self.msg_dict)
        with self.assertRaises(ValueError):
            send_message(socket, 'wrong dict')

    def test_get_message(self):
        socket_ok = SocketEmulation(self.test_answer_ok)
        socket_err = SocketEmulation(self.test_answer_error)
        self.assertEqual(get_message(socket_ok), self.test_answer_ok)
        self.assertEqual(get_message(socket_err), self.test_answer_error)

    def test_get_message_raises(self):
        socket = WrongRecvSocketEmulation(self.test_answer_ok)
        with self.assertRaises(ValueError):
            get_message(socket)


if __name__ == '__main__':
    unittest.main()
