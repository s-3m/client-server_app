from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime


class ServerDB:
    Base = declarative_base()

    class AllUsers(Base):
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_connection = Column(DateTime)

        def __init__(self, login):
            self.login = login
            self.last_connection = datetime.datetime.now()

    class ActiveUsers(Base):
        __tablename__ = 'active_users'

        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'), unique=True)
        ip = Column(String)
        port = Column(Integer)
        time_connection = Column(DateTime)

        def __init__(self, user, ip, port, time_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.time_connection = time_conn

    class LoginHistory(Base):
        __tablename__ = 'login_history'

        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        ip = Column(String)
        port = Column(Integer)
        time_connection = Column(DateTime)

        def __init__(self, user, ip, port, last_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_conn = last_conn

    class UserContacts(Base):
        __tablename__ = 'user_contacts'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('all_users.id'))
        contact = Column(ForeignKey('all_users.id'))

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory(Base):
        __tablename__ = 'user_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('all_users.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        result = self.session.query(self.AllUsers).filter_by(login=username)
        if result.count():
            user = result.first()
            user.last_connection = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(login=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        self.session.commit()

    def process_message(self, sender, recipient):
        sender = self.session.query(self.AllUsers).filter_by(login=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(login=recipient).first().id

        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        if not contact or self.session.query(self.UserContacts).filter_by(user=user.id, contact=contact.id).count():
            return
        contact_row = self.UserContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        if not contact:
            return

        self.session.query(self.UserContacts).filter(
            self.UserContacts.user == user.id, self.UserContacts.contact == contact.id
        ).delete()
        self.session.commit()

    def get_contacts(self, username):
        user = self.session.query(self.AllUsers).filter_by(login=username).one()

        query = self.session.query(self.UserContacts, self.AllUsers.login). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UserContacts.contact == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_connection,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)

        return query.all()

    def user_list(self):
        users = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_connection,
        )
        return users.all()

    def active_users_list(self):
        active_users = self.session.query(
            self.AllUsers.login,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.time_connection
        ).join(self.AllUsers)
        return active_users.all()

    def login_history(self, username=None):
        res = self.session.query(
            self.AllUsers.login,
            self.LoginHistory.time_connection,
            self.LoginHistory.ip,
            self.LoginHistory.port
        ).join(self.AllUsers)

        if username:
            res = res.filter(self.AllUsers.login == username)
        return res.all()


if __name__ == '__main__':
    db = ServerDB()
    db.user_login('user1', '127.0.0.2', 7777)
    db.user_login('user2', '127.0.0.3', 7777)


