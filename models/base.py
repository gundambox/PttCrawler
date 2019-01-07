import logging
import os
from typing import Dict, List

from sqlalchemy import DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class MyDateTime(DateTime):
    def __init__(self, timezone=False):
        super().__init__(timezone)

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is not None:
                return value
            else:
                return None
        return process

    def adapt(self, impltype, **kw):
        return MyDateTime(self.timezone)


class PttDatabase:
    DB_ENGINE = {
        'sqlite': 'sqlite:///{DB}'
    }

    def __init__(self, dbtype, username='', password='', dbname=''):

        dbtype = dbtype.lower()

        if dbtype in self.DB_ENGINE.keys():

            # folder = os.path.dirname(dbname)
            # if folder != '':
            #     if not os.path.exists(folder):
            #         os.makedirs(folder)

            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.engine = create_engine(engine_url)
            # Base.metadata.create_all(self.engine, checkfirst=True)
        else:
            raise ValueError("DBType is not found in DB_ENGINE")

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()

    def get_or_create(self, session, model, condition: Dict, values: Dict, auto_commit=True):
        instance = session.query(model).filter_by(**condition).first()
        if instance:
            return instance, False
        else:
            instance = model(**values)
            session.add(instance)
            if auto_commit:
                session.commit()
            else:
                session.flush()
            return instance, True

    def create(self, session, model, values: Dict, auto_commit=True):
        instance = model(**values)
        session.add(instance)
        if auto_commit:
            session.commit()
        else:
            session.flush()
        return instance

    def get(self, session, model, condition: Dict):
        instance = session.query(model).filter_by(**condition).first()
        return instance

    def get_list(self, session, model, condition: Dict) -> List:
        ins_list = session.query(model).filter_by(**condition).all()
        return ins_list

    def delete(self, session, model, condition: Dict, auto_commit=True):
        session.query(model).filter_by(**condition).delete()
        if auto_commit:
            session.commit()
        else:
            session.flush()

    def bulk_insert(self, session, objects, auto_commit=True):
        session.bulk_save_objects(objects)
        if auto_commit:
            session.commit()
        else:
            session.flush()

    def bulk_update(self, session, model, objects, auto_commit=True):
        o_list = []
        for o in objects:
            o_list.append(session.merge(model(**o)))

        session.add_all(o_list)
        if auto_commit:
            session.commit()
        else:
            session.flush()
