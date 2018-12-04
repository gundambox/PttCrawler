import argparse
from datetime import datetime
from typing import Dict, List

from ipwhois.asn import IPASN
from ipwhois.net import Net

from models import IpAsn, PttDatabase
from utils import load_config, log


class PttIpAsnCrawler(object):
    def __init__(self):
        pass

    def _init_crawler(self, arguments: Dict[str, str]):
        config_path = (arguments['config_path']
                       if arguments['config_path']
                       else 'config.ini')

        self.config = load_config(config_path)

        self.db_input = arguments['database'] or False

        self.db = PttDatabase(dbtype=self.config['Database']['Type'],
                              dbname=self.config['Database']['Name'])
        self.db_session = self.db.get_session()

    def _get_ip_list(self, arguments: Dict[str, str]):
        if self.db_input:
            ip_list = list(map(lambda ipasn: str(ipasn.ip),
                               self.db.get_list(self.db_session, IpAsn, {})))
        else:
            ip_list = arguments['ip_list'].split(',')

        return ip_list

    @log
    def _output_db(self, result: List[Dict[str, str]]):
        self.db.bulk_update(self.db_session, IpAsn, result)

    @log
    def go(self, arguments: Dict[str, str]):
        self._init_crawler(arguments)
        ip_list = self._get_ip_list(arguments)

        ip_result = []
        for ip in ip_list:
            net = Net(ip)
            obj = IPASN(net)
            result = {'ip': ip}
            result.update(obj.lookup())
            result['asn_date'] = datetime.strptime(
                result['asn_date'], '%Y-%m-%d')
            ip_result.append(result)

            if len(ip_result) % 100 == 0:
                self._output_db(ip_result)
                ip_result = []

        self._output_db(ip_result)


def parse_args() -> Dict[str, str]:
    parser = argparse.ArgumentParser()

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--ip-list',
                             type=str)
    input_group.add_argument('--database', action='store_true')

    # Config path
    parser.add_argument('--config-path',
                        type=str)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_args()
    crawler = PttIpAsnCrawler()
    crawler.go(args)


if __name__ == "__main__":
    main()
