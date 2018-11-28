import argparse
from crawler import article, asn, user
from enum import Enum
from export import PttExportHelper


class Cmd(Enum):
    crawler = 1
    export = 2


class CrawlerModule(Enum):
    article = 1
    asn = 2
    user = 3


def parse_argument():

    base_subparser = argparse.ArgumentParser(add_help=False)
    base_subparser.add_argument('--verbose',
                                action='store_true',
                                help='Show more debug messages.')
    base_subparser.add_argument('--config-path',
                                type=str,
                                help='Config ini file path.')

    parser = argparse.ArgumentParser(parents=[base_subparser])

    main_subparsers = parser.add_subparsers(dest='cmd', help='cmd help')
    main_subparsers.required = True

    crawler_parser = main_subparsers.add_parser('crawler',
                                                parents=[base_subparser])
    crawler_subparsers = crawler_parser.add_subparsers(dest='module',
                                                       help='crawler module help')

    parser_article = crawler_subparsers.add_parser('article',
                                                   parents=[base_subparser],
                                                   help='article module help')
    parser_article_group = parser_article.add_mutually_exclusive_group(
        required=True)
    parser_article_group.add_argument('--start-date',
                                      type=str)
    parser_article_group.add_argument('--index',
                                      type=int,
                                      metavar=('START_INDEX', 'END_INDEX'),
                                      nargs=2)
    parser_article.add_argument('--board-name',
                                type=str,
                                required=True)
    parser_article.add_argument('--json-prefix',
                                type=str,
                                default='')

    parser_asn = crawler_subparsers.add_parser('asn',
                                               parents=[base_subparser],
                                               help='ip_asn module help')
    parser_asn_group = parser_asn.add_mutually_exclusive_group(required=True)
    parser_asn_group.add_argument('--ip',
                                  type=str,
                                  help='ip list, separated by commas.')
    parser_asn_group.add_argument('--database',
                                  type=str,
                                  help='ip list from database.')

    parser_user = crawler_subparsers.add_parser('user',
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

    export_parser = main_subparsers.add_parser('export',
                                               parents=[base_subparser],
                                               help='export help')
    output_group = export_parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument('--format',
                              type=str,
                              choices=['ods', 'csv'])
    export_parser.add_argument('--output-folder',
                               type=str,
                               required=True)
    export_parser.add_argument('--output-prefix',
                               type=str,
                               default='')

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_argument()
    print(args)
    cmd = Cmd[args['cmd']]
    if cmd == Cmd.crawler:
        module = CrawlerModule[args['module']]
        if module == CrawlerModule.article:
            crawler = article.PttArticleCrawler()
            crawler.go(args)
        elif module == CrawlerModule.asn:
            crawler = asn.PttIpAsnCrawler()
            crawler.go(args)
        elif module == CrawlerModule.user:
            crawler = user.PttUserCrawler()
            crawler.go(args)
    elif cmd == Cmd.export:
        helper = PttExportHelper()
        helper.go(args)


if __name__ == "__main__":
    main()
