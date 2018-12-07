import argparse
import logging
from datetime import datetime
from typing import Dict, List

from ipwhois.asn import IPASN
from ipwhois.net import Net

from models import IpAsn, PttDatabase
from utils import load_config, log

from .crawler_arg import add_asn_arg_parser, get_base_parser


class PttIpAsnCrawler(object):
    def __init__(self, arguments: Dict):
        self.db_input = arguments['database'] or False
        self.ip_list = ('' if self.db_input else arguments['ip_list'])

        config_path = (arguments['config_path'] or 'config.ini')
        self.config = load_config(config_path)
        self.database_config = self.config['Database']

        self._init_database()

        if arguments['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

    def _init_database(self):
        self.db = PttDatabase(dbtype=self.database_config['Type'],
                              dbname=self.database_config['Name'])
        self.db_session = self.db.get_session()

    def _get_ip_list(self):
        if self.db_input:
            return list(map(lambda ipasn: str(ipasn.ip),
                            self.db_session.query(IpAsn).order_by(IpAsn.asn).all()))
        else:
            return self.ip_list.split(',')

    @log('Output_Database')
    def _output_database(self, result: List[Dict[str, str]]):
        self.db.bulk_update(self.db_session, IpAsn, result)

    @log()
    def crawling(self):
        ip_list = self._get_ip_list()

        ip_result = []
        for ip in ip_list:
            if ip:
                net = Net(ip)
                obj = IPASN(net)
                result = {'ip': ip}
                result.update(obj.lookup())
                result['asn_date'] = datetime.strptime(result['asn_date'],
                                                       '%Y-%m-%d')
                ip_result.append(result)

                if len(ip_result) % 100 == 0:
                    self._output_database(ip_result)
                    ip_result = []

        self._output_database(ip_result)


def parse_args() -> Dict[str, str]:
    base_subparser = get_base_parser()
    parser = argparse.ArgumentParser(parents=[base_subparser])
    add_asn_arg_parser(parser)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_args()
    crawler = PttIpAsnCrawler(args)
    crawler.crawling()


if __name__ == "__main__":
    main()
