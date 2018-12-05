import argparse
import csv
import os
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from typing import Dict, List

from pyexcel_ods import save_data
from sqlalchemy import case, func

from models import (Article, ArticleHistory, Board, IpAsn, PttDatabase, Push,
                    User, UserLastRecord)
from utils import load_config, log, valid_date_type


def parse_argument():
    base_subparser = argparse.ArgumentParser(add_help=False)
    base_subparser.add_argument('--verbose',
                                action='store_true',
                                help='Show more debug messages.')
    base_subparser.add_argument('--config-path',
                                type=str,
                                default='',
                                help='Config ini file path.')

    parser = argparse.ArgumentParser(parents=[base_subparser])

    parser.add_argument('--board-name',
                        type=str,
                        required=True)
    parser.add_argument('--date-range',
                        metavar=('START_DATE', 'END_DATE'),
                        nargs=2,
                        type=valid_date_type,
                        help='date in format "YYYY-MM-DD"',
                        required=True)

    parser.add_argument('--format',
                        type=str,
                        default='console',
                        choices=['ods', 'csv', 'console'])
    parser.add_argument('--output-folder',
                        type=str,
                        default='')
    parser.add_argument('--output-prefix',
                        type=str,
                        default='')
    args = parser.parse_args()
    arguments = vars(args)
    return arguments


"""
Input:看板名/時間(起)/時間(迄)
Output:看板名/時間(起)/時間(迄)/國內IP數量/國外IP數量
"""


class QueryHelper(object):
    def __init__(self, arguments: Dict[str, str]):
        config_path = (arguments['config_path']
                       if arguments['config_path']
                       else 'config.ini')

        self.start_date, self.end_date = arguments['date_range']
        self.board_name = arguments['board_name']
        self.file_format = arguments['format']

        self.config = load_config(config_path)
        self.output_folder = arguments['output_folder']
        self.output_prefix = arguments['output_prefix']

        self.db = PttDatabase(dbtype=self.config['Database']['Type'],
                              dbname=self.config['Database']['Name'])
        self.db_session = self.db.get_session()

    @log
    def _get_export_rows(self):
        rows = [['Type', 'Board', 'Start date',
                 'End date', 'TW Ip', 'Not TW Ip']]

        tw_ip_label = case(value=IpAsn.asn_country_code,
                           whens={'TW': True},
                           else_=False).label("TW_IP")

        article_res = self.db_session.query(Article, ArticleHistory, tw_ip_label) \
            .join(ArticleHistory, ArticleHistory.article_id == Article.id) \
            .join(Board, Board.id == Article.board_id) \
            .order_by(ArticleHistory.id) \
            .group_by(Article.id) \
            .join(IpAsn, IpAsn.ip == Article.post_ip) \
            .filter(Board.name == self.board_name).all()

        article_tw_ip = sum(1 for _, _, tw_ip in article_res
                            if tw_ip == True)
        article_not_tw_ip = sum(1 for _, _, tw_ip in article_res
                                if tw_ip == False)
        rows.append(['Article', self.board_name,
                     self.start_date, self.end_date, article_tw_ip, article_not_tw_ip])

        article_history_id_list = []
        for res in article_res:
            _, history, _ = res
            article_history_id_list.append(history.id)

        push_res = self.db_session.query(Push, tw_ip_label) \
            .join(IpAsn, IpAsn.ip == Push.push_ip) \
            .filter(Push.article_history_id.in_(article_history_id_list)).all()

        push_tw_ip = sum(1 for _,  tw_ip in push_res
                         if tw_ip == True)
        push_not_tw_ip = sum(1 for _,  tw_ip in push_res
                             if tw_ip == False)
        rows.append(['Push', self.board_name,
                     self.start_date, self.end_date, push_tw_ip, push_not_tw_ip])

        return rows

    def _print_rows(self):
        data = self._get_export_rows()
        for idx, row in enumerate(data):
            print('{:16} | {:16} | {:32} | {:32} | {:8} | {:8}'.format(
                *map(str, row)))
            if idx == 0:
                print('-----------------+------------------+----------------------------------+----------------------------------+----------+----------')

    def _export_ods(self):
        data = self._get_export_rows()

    def _export_csv(self):
        data = self._get_export_rows()

    def go(self):
        if self.file_format == 'console':
            self._print_rows()
        elif self.file_format == 'ods':
            self._export_ods()
        elif self.file_format == 'csv':
            self._export_csv()


def main():
    args = parse_argument()
    helper = QueryHelper(args)
    helper.go()


if __name__ == "__main__":
    main()
