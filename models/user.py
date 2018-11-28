import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from . import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer,
                Sequence('user_id_seq'),
                primary_key=True)
    username = Column(String(32),
                      unique=True,
                      nullable=False)
    login_times = Column(Integer,
                         nullable=True)
    valid_article_count = Column(Integer,
                                 nullable=True)

    last_record = relationship("UserLastRecord", backref="User",
                               order_by="desc(UserLastRecord.created_at)")

    def __repr__(self):
        return '<User(id={id}, \
username={username}, \
login_times={login_times}, \
valid_article_count={valid_article_count})>'.format(id=self.id,
                                                    username=self.username,
                                                    login_times=self.login_times,
                                                    valid_article_count=self.valid_article_count)


class UserLastRecord(Base):
    __tablename__ = 'user_last_record'
    id = Column('id',
                Integer,
                Sequence('user_last_record_id_seq'),
                primary_key=True)
    user_id = Column(Integer,
                     ForeignKey('user.id'),
                     nullable=False)
    last_login_datetime = Column(DateTime,
                                 nullable=False)
    last_login_ip = Column(String(40),
                           nullable=False)
    created_at = Column(DateTime,
                        nullable=False,
                        default=datetime.datetime.now)

    def __repr__(self):
        return '<UserLastRecord(id={id}, \
user_id={user_id}, \
last_login_datetime={last_login_datetime}, \
last_login_ip={last_login_ip}, \
created_at={created_at})>'.format(id=self.id,
                                  user_id=self.user_id,
                                  last_login_datetime=self.last_login_datetime,
                                  last_login_ip=self.last_login_ip,
                                  created_at=self.created_at)
