import argparse
import logging
from logging.handlers import RotatingFileHandler

from utils import valid_date_type

from . import CrawlerModule, PttArticleCrawler, PttIpAsnCrawler, PttUserCrawler
from .crawler_arg import (add_article_arg_parser, add_asn_arg_parser,
                          add_user_arg_parser, get_base_parser)


def parse_argument():
    base_subparser = get_base_parser()
    parser = argparse.ArgumentParser(parents=[base_subparser])

    main_subparsers = parser.add_subparsers(dest='module')
    main_subparsers.required = True

    parser_article = main_subparsers.add_parser('article',
                                                parents=[base_subparser],
                                                help='article module help')
    add_article_arg_parser(parser_article)

    parser_asn = main_subparsers.add_parser('asn',
                                            parents=[base_subparser],
                                            help='ip_asn module help')
    add_asn_arg_parser(parser_asn)

    parser_user = main_subparsers.add_parser('user',
                                             parents=[base_subparser],
                                             help='user module help')
    add_user_arg_parser(parser_user)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def _init_logger():
    formatter = logging.Formatter(fmt='[%(levelname)-8s] %(asctime)s %(message)s',
                                  datefmt='%Y/%m/%d %H:%M:%S')
    handler = RotatingFileHandler('PTTCrawler.log',
                                  maxBytes=1024 * 1024 * 1,  # 1 MB
                                  backupCount=100)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def main():
    args = parse_argument()
    module = CrawlerModule[args['module']]

    _init_logger()

    logging.info('Started')

    if module == CrawlerModule.article:
        crawler = PttArticleCrawler(args)
        crawler.crawling()
    elif module == CrawlerModule.asn:
        crawler = PttIpAsnCrawler(args)
        crawler.crawling()
    elif module == CrawlerModule.user:
        crawler = PttUserCrawler(args)
        crawler.crawling()

    logging.info('Finished')


if __name__ == '__main__':
    main()
