import sys
import unittest
from unittest import TestCase
sys.path.append('..')
from server import create_server_message


class TestServerSide(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_server_message_200(self):
        message = {'action': 'presence', 'time': 1.1, 'user': {'account_name': 'Guest'}}
        self.assertEqual(create_server_message(message), {"response": 200, "status": "OK"})

    def test_create_server_message_no_action(self):
        message = {'time': 1.1, 'user': {'account_name': 'Guest'}}
        self.assertEqual(create_server_message(message), {"response": 400, "error": "Bad Request"})

    def test_create_server_message_no_time(self):
        message = {'action': 'presence', 'user': {'account_name': ''}}
        self.assertEqual(create_server_message(message), {"response": 400, "error": "Bad Request"})

    def test_create_server_message_no_user(self):
        message = {'action': 'presence', 'time': 1.1}
        self.assertEqual(create_server_message(message), {"response": 400, "error": "Bad Request"})

    def test_create_server_message_empty_name(self):
        message = {'action': 'presence', 'time': 1.1, 'user': {'account_name': ''}}
        self.assertEqual(create_server_message(message), {"response": 400, "error": "Bad Request"})

    def test_create_server_message_wrong_action(self):
        message = {'action': 'hello', 'time': 1.1, 'user': {'account_name': ''}}
        self.assertEqual(create_server_message(message), {"response": 400, "error": "Bad Request"})


if __name__ == '__main__':
    unittest.main()
