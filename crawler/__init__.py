from enum import Enum

from crawler.article import PttArticleCrawler
from crawler.article_index import PttArticleIndexCrawler
from crawler.asn import PttIpAsnCrawler
from crawler.user import PttUserCrawler


class CrawlerModule(Enum):
    article_index = 1
    article = 2
    asn = 3
    user = 4
