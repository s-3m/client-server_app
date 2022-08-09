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

        def __int__(self, user, ip, port, time_connection):
            self.user = user
            self.port = port
            self.ip = ip
            self.time_connection = time_connection

    class LoginHistory(Base):
        __tablename__ = 'login_history'

        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('all_users.id'))
        ip = Column(String)
        port = Column(Integer)
        time_connection = Column(DateTime)

        def __int__(self, user, ip, port, time_connection):
            self.user = user
            self.port = port
            self.ip = ip
            self.time_connection = time_connection

    def __init__(self):
        self.engine = create_engine('sqlite:///server_base.db3', echo=False, pool_recycle=7200)

        self.Base.metadata.createall(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        result = self.session.query(self.AllUsers).filter_by(login=username).first()

        if result.count():
            user = result.first()
            user.last_connection = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(login=username).first()
        self.session.query(self.AllUsers).filter_by(user=user.id).first().delete()

        self.session.commit()

    def user_list(self):
        users = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_connection
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



