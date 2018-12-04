import argparse
import logging

from utils import valid_date_type

from . import CrawlerModule, PttArticleCrawler, PttIpAsnCrawler, PttUserCrawler


def parse_argument():
    base_subparser = argparse.ArgumentParser(add_help=False)
    base_subparser.add_argument('--verbose',
                                action='store_true',
                                help='Show more debug messages.')
    base_subparser.add_argument('--config-path',
                                type=str,
                                help='Config ini file path.')

    parser = argparse.ArgumentParser(parents=[base_subparser])

    main_subparsers = parser.add_subparsers(dest='module')
    main_subparsers.required = True

    parser_article = main_subparsers.add_parser('article',
                                                parents=[base_subparser],
                                                help='article module help')
    parser_article_group = parser_article.add_mutually_exclusive_group(
        required=True)
    parser_article_group.add_argument('--start-date',
                                      type=valid_date_type,
                                      help='start datetime in format "YYYY-MM-DD"')
    parser_article_group.add_argument('--index',
                                      type=int,
                                      metavar=('START_INDEX', 'END_INDEX'),
                                      nargs=2)
    parser_article.add_argument('--board-name',
                                type=str.lower,
                                required=True)
    parser_article.add_argument('--json-prefix',
                                type=str,
                                default='')

    parser_asn = main_subparsers.add_parser('asn',
                                            parents=[base_subparser],
                                            help='ip_asn module help')
    parser_asn_group = parser_asn.add_mutually_exclusive_group(required=True)
    parser_asn_group.add_argument('--ip',
                                  type=str,
                                  help='ip list, separated by commas.')
    parser_asn_group.add_argument('--database',
                                  action='store_true',
                                  help='ip list from database.')

    parser_user = main_subparsers.add_parser('user',
                                             parents=[base_subparser],
                                             help='user module help')
    parser_user_group = parser_user.add_mutually_exclusive_group(required=True)
    parser_user_group.add_argument('--id',
                                   type=str,
                                   help='ptt user id, separated by commas.')
    parser_user_group.add_argument('--database',
                                   action='store_true',
                                   help='ptt user id from database.')
    parser_user.add_argument('--json-prefix',
                             type=str,
                             default='')

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_argument()
    module = CrawlerModule[args['module']]
    logging.basicConfig(format='[%(levelname)-8s] %(asctime)s %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S',
                        filename='PTTCrawler.log',
                        level=logging.INFO)
    logging.info('Started')

    if module == CrawlerModule.article:
        crawler = PttArticleCrawler()
        crawler.go(args)
    elif module == CrawlerModule.asn:
        crawler = PttIpAsnCrawler()
        crawler.go(args)
    elif module == CrawlerModule.user:
        crawler = PttUserCrawler()
        crawler.go(args)

    logging.info('Finished')


if __name__ == '__main__':
    main()
