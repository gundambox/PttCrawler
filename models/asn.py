from datetime import datetime
from sqlalchemy import Column, DateTime, String

from . import Base


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


class IpAsn(Base):
    __tablename__ = 'ip_asn'
    ip = Column(String(40),
                primary_key=True)
    asn = Column(String(256),
                 nullable=True)
    asn_date = Column(MyDateTime,
                      nullable=True)
    asn_registry = Column(String(256),
                          nullable=True)
    asn_cidr = Column(String(256),
                      nullable=True)
    asn_country_code = Column(String(4),
                              nullable=True)
    asn_description = Column(String(256),
                             nullable=True)
    asn_raw = Column(String,
                     nullable=True)
