from datetime import datetime
from sqlalchemy import Column, DateTime, String

from . import Base, MyDateTime


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
