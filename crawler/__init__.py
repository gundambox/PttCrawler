from enum import Enum

from .article import PttArticleCrawler
from .asn import PttIpAsnCrawler
from .user import PttUserCrawler


class CrawlerModule(Enum):
    article = 1
    asn = 2
    user = 3
