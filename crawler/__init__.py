from enum import Enum

from .article import PttArticleCrawler
from .article_index import PttArticleIndexCrawler
from .asn import PttIpAsnCrawler
from .user import PttUserCrawler


class CrawlerModule(Enum):
    article_index = 1
    article = 2
    asn = 3
    user = 4
