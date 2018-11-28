from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from . import Base


class Board(Base):
    __tablename__ = 'board'
    id = Column(Integer,
                Sequence('board_id_seq'),
                primary_key=True)
    name = Column(String(64),
                  nullable=False)

    articles = relationship("Article", backref="Board")


class Article(Base):
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
    post_datetime = Column(DateTime(20),
                           nullable=False)
    post_ip = Column(String(20),
                     nullable=False)

    user = relationship("User", backref="Article")
    board = relationship("Board", backref="Article")
    history = relationship("ArticleHistory", backref="Article",
                           order_by="desc(ArticleHistory.end_at)")

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
                   nullable=False)
    content = Column(String,
                     nullable=False)
    start_at = Column(DateTime,
                      nullable=False)
    end_at = Column(DateTime,
                    nullable=False)

    article = relationship("Article", backref="ArticleHistory")
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
    article_history = relationship("ArticleHistory", backref="Push")
    user = relationship("User", backref="Push")
