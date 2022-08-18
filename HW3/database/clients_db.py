from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker, declarative_base
import datetime


class ClientDB:
    Base = declarative_base()

    class KnownUsers(Base):
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        username = Column(String)

        def __init__(self, username):
            self.username = username

    class MessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        from_user = Column(String)
        to_user = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, from_user, to_user, message):
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)

        def __init__(self, name):
            self.name = name

    def __init__(self, name):
        self.engine = create_engine(
            f'sqlite:///clients_{name}_db.db3',
            echo=False, pool_recycle=7200,
            connect_args={'check_same_thread': False}
        )

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact = self.Contacts(contact)
            self.session.add(contact)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def add_users(self, user_list):
        self.session.query(self.KnownUsers).delete()
        for user in user_list:
            user = self.KnownUsers(user)
            self.session.add(user)
            self.session.commit()

    def save_message(self, from_user, to_user, message):
        message = self.MessageHistory(from_user, to_user, message)
        self.session.add(message)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, from_who=None, to_who=None):
        result = self.session.query(self.MessageHistory)
        if from_who:
            result = result.filter_by(from_user=from_who)
        if to_who:
            result = result.filter_by(to_user=to_who)
        return [(history.from_user, history.to_user, history.message) for history in result.all()]


if __name__ == '__main__':
    test_db = ClientDB('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')
    test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    test_db.save_message('test1', 'test2',
                         f'Привет! я тестовое сообщение от {datetime.datetime.now().replace(microsecond=0)}!')
    test_db.save_message('test2', 'test1',
                         f'Привет! я другое тестовое сообщение от {datetime.datetime.now().replace(microsecond=0)}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('test1'))
    print(test_db.check_user('test10'))
    print(test_db.get_history('test2'))
    print(test_db.get_history(to_who='test2'))
    print(test_db.get_history('test3'))
    test_db.del_contact('test4')
    print(test_db.get_contacts())
