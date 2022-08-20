import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt


logger = logging.getLogger('client_dist')

class DelContactDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выберите контакт для удаления:')
        # Удаляем диалог, если окно было закрыто преждевременно
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Делаем это окно модальным (т.е. поверх других)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)
        # заполнитель контактов для удаления
        self.selector.addItems(sorted(self.database.get_contacts()))

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)


        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from database import clients_db
    database = clients_db.ClientDB('test1')
    window = DelContactDialog(database)
    # при подключении контакты удаляются, а затем добавляются с сервера
    # поэтому для проверки сами вручную добавляем контакт для списка удаления
    database.add_contact('test1')
    database.add_contact('test2')
    print(database.get_contacts())
    window.selector.addItems(sorted(database.get_contacts()))
    window.show()
    app.exec_()
