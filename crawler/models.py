import datetime
import os
from typing import Dict

from sqlalchemy import (Column, DateTime, ForeignKey, Integer,
                        PrimaryKeyConstraint, Sequence, String, Table,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

BaseModel = declarative_base()


class User(BaseModel):
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

    last_record = relationship(
        "UserLastRecord", backref="User", lazy='dynamic')

    def __repr__(self):
        return '<User(id={id}, \
username={username}, \
login_times={login_times}, \
valid_article_count={valid_article_count})>'.format(id=self.id,
                                                    username=self.username,
                                                    login_times=self.login_times,
                                                    valid_article_count=self.valid_article_count)


class UserLastRecord(BaseModel):
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


class Board(BaseModel):
    __tablename__ = 'board'
    id = Column(Integer,
                Sequence('board_id_seq'),
                primary_key=True)
    name = Column(String(64),
                  nullable=False)

    articles = relationship("Article", backref="Board")


class Article(BaseModel):
    __tablename__ = 'article'
    id = Column(Integer,
                Sequence('article_id_seq'),
                primary_key=True)
    web_id = Column(String(20),
                    nullable=False)
    user_id = Column(Integer,
                     ForeignKey('user.id'),
                     nullable=False)
    board_id = Column(Integer,
                      ForeignKey('board.id'),
                      nullable=False)
    post_datetime = Column(String(20),
                           nullable=False)
    post_ip = Column(String(20),
                     nullable=False)

    board = relationship("Board", backref="Article")
    histroy = relationship("ArticleHistory", backref="Article",
                           order_by="desc(ArticleHistory.end_at)")


class ArticleHistory(BaseModel):
    __tablename__ = 'article_history'
    id = Column(Integer,
                Sequence('article_history_id_seq'),
                primary_key=True)
    article_id = Column(Integer,
                        ForeignKey('article.id'),
                        nullable=False)
    title = Column(String(64),
                   nullable=False)
    content = Column(String,
                     nullable=False)
    start_at = Column(DateTime,
                      nullable=False)
    end_at = Column(DateTime,
                    nullable=False)

    push_list = relationship("Push", backref="ArticleHistory",
                             order_by="desc(Push.push_datetime)")


class Push(BaseModel):
    __tablename__ = 'push'
    id = Column(Integer,
                Sequence('push_id_seq'),
                primary_key=True)
    article_history_id = Column(Integer,
                                ForeignKey('article_history.id'),
                                nullable=False)
    floor = Column(Integer,
                   nullable=False)
    push_tag = Column(String(2),
                      nullable=False)
    push_user_id = Column(Integer,
                          ForeignKey('user.id'),
                          nullable=False)
    push_content = Column(String(128),
                          nullable=False)
    push_ip = Column(String(40),
                     nullable=True)
    push_datetime = Column(DateTime,
                           nullable=False)


class IpAsn(BaseModel):
    __tablename__ = 'ip_asn'
    ip = Column(String(40),
                primary_key=True)
    asn = Column(String(256),
                 nullable=False)
    asn_date = Column(DateTime,
                      nullable=False)
    asn_registry = Column(String(256),
                          nullable=False)
    asn_cidr = Column(String(256),
                      nullable=False)
    asn_country_code = Column(String(4),
                              nullable=False)
    asn_description = Column(String(256),
                             nullable=False)
    asn_raw = Column(String,
                     nullable=True)


class PttDatabase:
    DB_ENGINE = {
        'sqlite': 'sqlite:///{DB}'
    }

    def __init__(self, dbtype, username='', password='', dbname=''):

        dbtype = dbtype.lower()

        if dbtype in self.DB_ENGINE.keys():

            folder = os.path.dirname(dbname)
            if folder != '':
                if not os.path.exists(folder):
                    os.makedirs(folder)

            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.engine = create_engine(engine_url)
            BaseModel.metadata.create_all(self.engine, checkfirst=True)
        else:
            raise ValueError("DBType is not found in DB_ENGINE")

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()

    def get_or_create(self, session, model, condition: Dict, values: Dict):
        instance = session.query(model).filter_by(**condition).first()
        if instance:
            return instance, False
        else:
            instance = model(**values)
            session.add(instance)
            session.commit()
            return instance, True

    def create(self, session, model, values: Dict):
        instance = model(**values)
        session.add(instance)
        session.commit()
        return instance

    def get(self, session, model, condition: Dict):
        instance = session.query(model).filter_by(**condition).first()
        return instance

    def delete(self, session, model, condition: Dict):
        session.query(model).filter_by(**condition).delete()
        session.commit()

    def bulk_insert(self, session, objects):
        session.bulk_save_objects(objects)
        session.commit()
