import argparse
import csv
import os
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from typing import Dict, List

from pyexcel_ods import save_data
from sqlalchemy import func

from models import (Article, ArticleHistory, Board, IpAsn, PttDatabase, Push,
                    User, UserLastRecord)
from utils import load_config


class ExportFormat(Enum):
    ods = 1
    csv = 2


class PttExportHelper(object):
    def __init__(self):
        pass

    def _init_helper(self, arguments: Dict[str, str]):
        config_path = (arguments['config_path']
                       if arguments['config_path']
                       else 'config.ini')
        self.config = load_config(config_path)
        self.file_format = ExportFormat[arguments['format']]
        self.output_folder = arguments['output_folder']
        self.output_prefix = arguments['output_prefix']

        self.db = PttDatabase(dbtype=self.config['Database']['Type'],
                              dbname=self.config['Database']['Name'])
        self.db_session = self.db.get_session()

    def _get_export_rows(self):
        article_rows = [['Atricle.web_id', 'Article.board', 'Atricle.author', 'Atricle.title', 'Atricle.cotent',
                         'Atricle.post_ip', 'Atricle.post_ip.asn', 'Atricle.post_ip.asn_date', 'Atricle.post_ip.asn_registry',
                         'Atricle.post_ip.asn_cidr', 'Atricle.post_ip.asn_country_code', 'Atricle.post_ip.asn_description',
                         'Article.post_datetime', 'Article.last_modified_time']]
        push_rows = [['Push.article_web_id', 'Push.username', 'Push.tag', 'Push.content', 'Push.ip',
                      'Push.ip.asn', 'Push.ip.asn_cidr', 'Push.ip.asn_country_code',
                      'Push.ip.asn_date', 'Push.ip.asn_description', 'Push.ip.asn_registry', 'Push.datatime']]
        user_rows = [['User.username', 'User.login_times', 'User.valid_article_count',
                      'User.last_login_datetime', 'User.last_login_ip',
                      'User.last_login_ip.asn', 'User.last_login_ip.asn_date', 'User.last_login_ip.asn_registry',
                      'User.last_login_ip.asn_cidr', 'User.last_login_ip.asn_country_code', 'User.last_login_ip.asn_description']]

        data = OrderedDict()
        article_list = self.db_session.query(
            Article).order_by(Article.post_datetime).all()

        for article in article_list:
            article_row = [article.web_id,
                           article.board.name, article.user.username]

            last_history = article.history[0]
            article_row += [last_history.title, last_history.content]

            article_ip_asn = self.db_session.query(
                IpAsn).filter_by(ip=article.post_ip).first()
            if article_ip_asn:
                article_row += [article_ip_asn.ip, article_ip_asn.asn, str(article_ip_asn.asn_date),
                                article_ip_asn.asn_registry, article_ip_asn.asn_cidr, article_ip_asn.asn_country_code,
                                article_ip_asn.asn_description]
            else:
                article_row += [article.post_ip, '', '', '', '', '', '']

            article_row += [str(article.post_datetime),
                            str(last_history.end_at)]

            article_rows.append(article_row)

            for push in last_history.push_list:
                push_row = [article.web_id]
                push_row += [push.user.username,
                             push.push_tag, push.push_content]
                push_ip_asn = self.db_session.query(
                    IpAsn).filter_by(ip=push.push_ip).first()
                if push_ip_asn:
                    push_row += [push_ip_asn.ip, push_ip_asn.asn or '', str(push_ip_asn.asn_date or ''),
                                 push_ip_asn.asn_registry or '', push_ip_asn.asn_cidr or '', push_ip_asn.asn_country_code or '',
                                 push_ip_asn.asn_description or '']
                else:
                    push_row += [push.push_ip, '', '', '', '', '', '']
                push_row += [push.push_datetime.strftime('%m/%d %H:%M:%S')]
                push_rows.append(push_row)

        user_list = self.db_session.query(User).all()
        for user in user_list:
            user_row = []
            if user.last_record:
                user_last_record = user.last_record[0]
                user_ip_asn = self.db_session.query(IpAsn).filter_by(
                    ip=user_last_record.last_login_ip).first()
                user_row += [user.username, user.login_times, user.valid_article_count,
                             str(user_last_record.last_login_datetime), user_last_record.last_login_ip]
                user_row += [user_ip_asn.asn or '', str(user_ip_asn.asn_date or ''),
                             user_ip_asn.asn_registry or '', user_ip_asn.asn_cidr or '', user_ip_asn.asn_country_code or '',
                             user_ip_asn.asn_description or '']
            else:
                user_row += ['', '', '', '', '', '', '', '', '', '', '']
            user_rows.append(user_row)
        data.update({'Article': article_rows})
        data.update({'Push': push_rows})
        data.update({'User': user_rows})

        return data

    def _export_csv(self):
        data = self._get_export_rows()

        for (sheet, rows) in data.items():
            output_filename = 'Ptt_{sheet}_report_{export_datetime}'.format(sheet=sheet,
                                                                            export_datetime=datetime.now().strftime('%Y-%m-%d'))
            csv_path = os.path.join(self.output_folder, '{prefix}{filename}.{file_format}'.format(prefix=self.output_prefix,
                                                                                                  filename=output_filename,
                                                                                                  file_format=self.file_format.name))
            with open(csv_path, 'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',')
                for row in rows:
                    csvwriter.writerow(row)

    def _export_ods(self):
        output_filename = 'Ptt_report_{export_datetime}'.format(
            export_datetime=datetime.now().strftime('%Y-%m-%d'))

        output_path = os.path.join(self.output_folder, '{prefix}{filename}.{file_format}'.format(prefix=self.output_prefix,
                                                                                                 filename=output_filename,
                                                                                                 file_format=self.file_format.name))
        data = self._get_export_rows()
        save_data(output_path, data)

    def go(self, arguments: Dict[str, str]):
        self._init_helper(arguments)

        if self.file_format == ExportFormat.ods:
            self._export_ods()
        elif self.file_format == ExportFormat.csv:
            self._export_csv()
        else:
            raise ValueError('File format error.')


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

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument('--format',
                              type=str,
                              choices=['ods', 'csv'])
    parser.add_argument('--output-folder',
                        type=str,
                        required=True)
    parser.add_argument('--output-prefix',
                        type=str,
                        default='')
    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_argument()
    helper = PttExportHelper()
    helper.go(args)


if __name__ == "__main__":
    main()
