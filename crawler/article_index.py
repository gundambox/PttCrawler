import argparse
import logging
import re
import time
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from sqlalchemy import func

from models import ArticleIndex, Board, PttDatabase
from utils import load_config, log

from .crawler_arg import add_article_index_arg_parser, get_base_parser


class PttArticleIndexCrawler(object):
    PTT_URL = 'https://www.ptt.cc'
    PTT_Board_Format = '/bbs/{board}/index{index}.html'

    def __init__(self, arguments: Dict[str, str]):
        def get_default_start_url(board_name):
            last_index = self._getLastPage(board_name)
            return last_index, (self.PTT_URL + self.PTT_Board_Format.format(board_name, last_index))

        config_path = (arguments['config_path'] or 'config.ini')

        self._init_config(config_path)
        self._init_database()

        self.board_name = arguments['board_name']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0'}
        self.cookies = {'over18': '1'}

        self.before = arguments['before']
        logging.info('{}'.format('Before' if self.before else 'After'))
        if arguments['before']:
            if arguments['index']:
                self.end_index = arguments['index']
            else:
                self.end_index = self._getDBLastPage()
                if not self.end_index:
                    self.end_index = self._getLastPage()
            self.start_index = 1
        else:
            if arguments['index']:
                self.start_index = arguments['index']
            else:
                self.start_index = self._getDBLastPage()
                if not self.start_index:
                    self.start_index = self._getLastPage()
            self.end_index = self._getLastPage()

        self.start_url = (self.PTT_URL + self.PTT_Board_Format.format(board=self.board_name,
                                                                      index=self.end_index))

    def _init_config(self, config_path: str):
        self.config = load_config(config_path)
        self.article_config = self.config['PttArticle']
        self.database_config = self.config['Database']

        self.NEXT_PAGE_DELAY_TIME = float(
            self.article_config['NextPageDelaytime'])

    def _init_database(self):
        self.db = PttDatabase(dbtype=self.database_config['Type'],
                              dbname=self.database_config['Name'])
        self.db_session = self.db.get_session()

    def _getDBLastPage(self):
        board, _ = self.db.get_or_create(self.db_session,
                                         Board,
                                         {'name': self.board_name},
                                         {'name': self.board_name})
        index_func = (func.min if self.before else func.max)
        article_index_res = self.db_session \
            .query(ArticleIndex.board_id, index_func(ArticleIndex.index)) \
            .group_by(ArticleIndex.board_id) \
            .filter(ArticleIndex.board_id == board.id) \
            .all()

        if article_index_res and len(article_index_res) > 0:
            for _, index in article_index_res:
                return index
        else:
            return None

    def _getLastPage(self, timeout=3):
        """Ref: https://github.com/jwlin/ptt-web-crawler/blob/f8c04076004941d3f7584240c86a95a883ae16de/PttWebCrawler/crawler.py#L189"""
        resp = requests.get(
            url=self.PTT_URL +
            self.PTT_Board_Format.format(board=self.board_name, index=''),
            headers=self.headers,
            cookies=self.cookies,
            timeout=timeout
        )
        self.cookies = resp.cookies
        self.cookies['over18'] = '1'
        content = resp.content.decode('utf-8')
        first_page = re.search(
            r'href="/bbs/\w+/index(\d+).html">&lsaquo;', content)
        if first_page is None:
            return 1
        return int(first_page.group(1)) + 1

    @log('Output_Database')
    def _output_database(self, result: List[Dict[str, object]]):
        self.db.bulk_update(self.db_session, ArticleIndex, result)

    def crawling(self):
        board = self.db.get(self.db_session,
                            Board,
                            {'name': self.board_name})

        logging.info('Index range: %d ~ %d',
                     self.start_index, self.end_index)
        while self.end_index >= self.start_index:
            ptt_index_url = (self.PTT_URL +
                             self.PTT_Board_Format).format(board=self.board_name,
                                                           index=self.end_index)
            logging.info('Processing index: %d, Url = %s',
                         self.end_index, ptt_index_url)

            resp = requests.get(url=ptt_index_url,
                                headers=self.headers,
                                cookies=self.cookies,
                                timeout=None)
            self.cookies = resp.cookies
            self.cookies['over18'] = '1'

            if resp.status_code != 200:
                logging.error('Processing index error, status_code = %d, Url = %s',
                              resp.status_code, ptt_index_url)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')
            divs = soup.find("div",
                             "r-list-container action-bar-margin bbs-screen")
            children = divs.findChildren("div",
                                         recursive=False)

            article_list = []

            for div in children:
                # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                try:
                    if 'r-list-sep' in div['class']:
                        break
                    elif 'r-ent' in div['class']:
                        try:
                            href = div.find('a')['href']
                            link = self.PTT_URL + href
                            article_id = re.sub(
                                '\.html', '', href.split('/')[-1])

                            article_list.append({
                                'web_id': article_id,
                                'board_id': board.id,
                                'index': self.end_index})

                            logging.debug('Processing article: %s, Url = %s',
                                          article_id, link)
                        except:
                            pass
                except Exception as e:
                    logging.exception(
                        'Processing article error, Url = %s', link)

            self._output_database(article_list)

            self.end_index -= 1
            time.sleep(self.NEXT_PAGE_DELAY_TIME)


def parse_args() -> Dict[str, str]:
    base_subparser = get_base_parser()
    parser = argparse.ArgumentParser(parents=[base_subparser])
    add_article_index_arg_parser(parser)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_args()
    crawler = PttArticleIndexCrawler(args)
    crawler.crawling()


if __name__ == "__main__":
    main()
