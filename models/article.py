import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import backref, relationship

from . import Base, MyDateTime


class Board(Base):
    __tablename__ = 'board'
    id = Column(Integer,
                Sequence('board_id_seq'),
                primary_key=True)
    name = Column(String(64),
                  nullable=False)

    articles = relationship("Article", backref="Board")


class ArticleIndex(Base):
    __tablename__ = 'article_index'
    web_id = Column(String(20),
                    primary_key=True)
    board_id = Column(Integer,
                      ForeignKey('board.id'),
                      nullable=False)
    index = Column(Integer,
                   nullable=False)

    board = relationship("Board", backref="ArticleIndex")


class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer,
                Sequence('article_id_seq'),
                primary_key=True)
    web_id = Column(String(20),
                    ForeignKey('article_index.web_id'),
                    nullable=False)
    user_id = Column(Integer,
                     ForeignKey('user.id'),
                     nullable=False)
    board_id = Column(Integer,
                      ForeignKey('board.id'),
                      nullable=False)
    post_datetime = Column(MyDateTime,
                           nullable=True)
    post_ip = Column(String(20),
                     nullable=True)

    user = relationship("User", backref="Article")
    board = relationship("Board", backref="Article")
    history = relationship("ArticleHistory", backref="Article",
                           order_by="desc(ArticleHistory.start_at)")

    def __repr__(self):
        return '<Article(id={id}, \
web_id={web_id}, \
author={username}, \
board={board_name}, \
post_datetime={post_datetime}, \
post_ip={post_ip})>'.format(id=self.id,
                            web_id=self.web_id,
                            username=self.user.username,
                            board_name=self.board.name,
                            post_datetime=self.post_datetime,
                            post_ip=self.post_ip)


class ArticleHistory(Base):
    __tablename__ = 'article_history'
    id = Column(Integer,
                Sequence('article_history_id_seq'),
                primary_key=True)
    article_id = Column(Integer,
                        ForeignKey('article.id'),
                        nullable=False)
    title = Column(String(64),
                   nullable=True)
    content = Column(String,
                     nullable=False)
    start_at = Column(DateTime,
                      nullable=False,
                      default=datetime.datetime.now)
    end_at = Column(DateTime,
                    nullable=False,
                    default=datetime.datetime.now)

    article = relationship(
        "Article", backref="ArticleHistory")
    push_list = relationship("Push", backref="ArticleHistory",
                             order_by="desc(Push.push_datetime)")

    def __repr__(self):
        return '<ArticleHistory(id={id}, \
web_id={web_id}, \
author={username}, \
board={board_name}, \
title={title}, \
post_datetime={post_datetime}, \
post_ip={post_ip})>'.format(id=self.id,
                            web_id=self.article.web_id,
                            username=self.article.user.username,
                            board_name=self.article.board.name,
                            title=self.title,
                            post_datetime=self.article.post_datetime,
                            post_ip=self.article.post_ip)


class Push(Base):
    __tablename__ = 'push'
    id = Column(Integer,
                Sequence('push_id_seq'),
                primary_key=True)
    article_history_id = Column(Integer,
                                ForeignKey('article_history.id',
                                           ondelete='CASCADE'),
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
    push_datetime = Column(MyDateTime,
                           nullable=True)
    article_history = relationship("ArticleHistory",
                                   backref=backref("Push", cascade='all,delete'))
    # article_history = relationship("ArticleHistory",
    #                                backref=backref("Push", passive_deletes=True))
    user = relationship("User", backref="Push")

    def __repr__(self):
        return '<Article(id={id}, \
article_history_id={article_history_id}, \
floor={floor}, \
push_tag={push_tag}, \
push_user_id={push_user_id}, \
push_content={push_content}, \
push_ip={push_ip}, \
push_datetime={push_datetime})>'.format(id=self.id,
                                        article_history_id=self.article_history_id,
                                        floor=self.floor,
                                        push_tag=self.push_tag,
                                        push_user_id=self.push_user_id,
                                        push_content=self.push_content,
                                        push_ip=self.push_ip,
                                        push_datetime=self.push_datetime)
