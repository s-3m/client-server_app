import sys
import unittest
from unittest import TestCase
sys.path.append('..')
from client import create_client_message, process_answer


class TestClientSide(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_presence_message(self):
        message = create_client_message('presence')
        message['time'] = 1.1
        self.assertEqual(message, {"action": "presence", "time": 1.1, "user": {"account_name": "Guest"}})

    def test_def_process_answer_200(self):
        self.assertEqual(process_answer({'response': 200, 'status': 'OK'}), 'Cоединение с сервером установлено. Код - 200. Статус: OK')

    def test_def_process_answer_400(self):
        self.assertEqual(process_answer({'response': 400, 'error': 'Bad Request'}), '400 : Bad Request')

    def test_def_process_answer_ValueError(self):
        with self.assertRaises(ValueError):
            process_answer({'status': 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
