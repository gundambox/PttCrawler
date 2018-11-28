import argparse
import codecs
import json
import re
import sys
import time
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from models import (Article, ArticleHistory, Board, IpAsn, PttDatabase, Push,
                    User, UserLastRecord)
from PttWebCrawler.crawler import PttWebCrawler
from utils import load_config


class PttArticleCrawler(PttWebCrawler):

    PTT_URL = 'https://www.ptt.cc'
    PTT_Board_Format = '/bbs/{board}/index{index}.html'
    DELAY_TIME = 1.0
    NEXT_PAGE_DELAY_TIME = 5.0

    def __init__(self):
        super().__init__(as_lib=True)

    def _init_config(self, config_path: str):
        self.config = load_config(config_path)

        if self.config['PttArticle']['Output'] == 'both':
            self.json_output = True
            self.database_output = True
        elif self.config['PttArticle']['Output'] == 'database':
            self.json_output = False
            self.database_output = True
        elif self.config['PttArticle']['Output'] == 'json':
            self.json_output = True
            self.database_output = False
        else:
            self.json_output = False
            self.database_output = False

    def _init_database(self):
        self.db = PttDatabase(dbtype=self.config['Database']['Type'],
                              dbname=self.config['Database']['Name'])
        self.db_session = self.db.get_session()

    def _init_crawler(self, arguments: Dict[str, str]):
        config_path = (arguments['config_path']
                       if arguments['config_path']
                       else 'config.ini')

        self._init_config(config_path)
        self._init_database()

    def _output_json(self, result: Dict[str, object], json_prefix, board, index):
        current_time_str = datetime.now().strftime('%Y-%m-%d_result')
        json_path = '{prefix}{board}_{index}_{time}.json'.format(prefix=json_prefix,
                                                                 board=board,
                                                                 index=index,
                                                                 time=current_time_str)

        with codecs.open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile, sort_keys=True,
                      indent=4, ensure_ascii=False)

    def _output_database(self, result: List[Dict[str, object]]):

        def parser_push_ipdatetime(push_ipdatetime):
            match = re.search(
                r'([\d.]*)\W?(\d{2}\/\d{2}\ \d{2}:\d{2})', push_ipdatetime)
            if match:
                push_ip = match.group(1)
                push_datetime = datetime.strptime(
                    match.group(2), "%m/%d %M:%S")

                return push_ip, push_datetime
            else:
                return None

        def parse_author(author):
            match = re.search(r'([\S]*)\D\((.*)\)', author)
            if match:
                return match.group(1)
            else:
                return None

        for record in result:
            try:
                author_username = parse_author(record['author'])
                author_conditon = {'username': author_username}
                author_values = {'username': author_username,
                                 'login_times': 0,
                                 'valid_article_count': 0}
                user, is_new_user = self.db.get_or_create(self.db_session,
                                                          User,
                                                          author_conditon,
                                                          author_values)
                board, is_new_board = self.db.get_or_create(self.db_session, Board,
                                                            {'name': record['board']},
                                                            {'name': record['board']})
                article, is_new_article = self.db.get_or_create(self.db_session, Article,
                                                                {'web_id': record['article_id']},
                                                                {'web_id': record['article_id'],
                                                                 'user_id': user.id,
                                                                 'board_id': board.id,
                                                                 'post_datetime': datetime.strptime(record['date'],
                                                                                                    '%a %b %d %H:%M:%S %Y'),
                                                                 'post_ip': record['ip']})
                aritcle_ipasn, _ = self.db.get_or_create(self.db_session,
                                                         IpAsn,
                                                         {'ip': record['ip']},
                                                         {'ip': record['ip']})

                # 1. 新文章
                # 2. 舊文章發生修改
                # => 新增歷史記錄
                if is_new_article or article.history[0].content != record['content']:
                    history = self.db.create(self.db_session, ArticleHistory,
                                             {'article_id': article.id,
                                              'title': record['article_title'],
                                              'content': record['content'],
                                              'start_at': datetime.now(),
                                              'end_at': datetime.now()})
                    if not is_new_article:
                        self.db.delete(self.db_session, Push, {
                            'article_history_id': history.id})
                # 舊文章
                else:
                    history = article.history[0]

                # 更新到最近的文章歷史記錄推文
                push_list = []
                for (floor, message) in enumerate(record['messages']):
                    push_user_condition = {'username': message['push_userid']}
                    push_user_values = {'username': message['push_userid'],
                                        'login_times': None,
                                        'valid_article_count': None}
                    push_user, is_new_push_user = self.db.get_or_create(self.db_session,
                                                                        User,
                                                                        push_user_condition,
                                                                        push_user_values)
                    push_ip, push_datetime = parser_push_ipdatetime(
                        message['push_ipdatetime'])

                    push_list.append(Push(article_history_id=history.id,
                                          floor=(floor+1),
                                          push_tag=message['push_tag'],
                                          push_user_id=push_user.id,
                                          push_content=message['push_content'],
                                          push_ip=push_ip,
                                          push_datetime=push_datetime))
                    push_ipasn, _ = self.db.get_or_create(self.db_session,
                                                          IpAsn,
                                                          {'ip': push_ip},
                                                          {'ip': push_ip})

                self.db.bulk_insert(self.db_session, push_list)
            except Exception as e:
                raise e

    def go(self, arguments: Dict[str, str]):
        self._init_crawler(arguments)

        board = arguments['board_name']
        timeout = int(self.config['PttArticle']['Timeout'])

        start_date = (datetime.strptime(arguments['start_date'], '%Y-%m-%d')
                      if arguments['start_date']
                      else None)

        start_index, end_index = ((arguments['index'])
                                  if arguments['index']
                                  else (1, self.getLastPage(board)))
        last_page = end_index

        self.DELAY_TIME = float(self.config['PttArticle']['Delaytime'])
        self.NEXT_PAGE_DELAY_TIME = float(
            self.config['PttArticle']['NextPageDelaytime'])
        while last_page >= start_index:
            resp = requests.get(
                url=(self.PTT_URL +
                     self.PTT_Board_Format).format(board=board, index=last_page),
                cookies={'over18': '1'},
                timeout=timeout
            )
            if resp.status_code != 200:
                raise RuntimeError('invalid url: {url}'.format(url=resp.url))

            soup = BeautifulSoup(resp.text, 'html.parser')
            divs = soup.find_all("div", "r-ent")

            article_list = []

            for div in divs:
                try:
                    # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                    href = div.find('a')['href']
                    link = self.PTT_URL + href
                    article_id = re.sub('\.html', '', href.split('/')[-1])
                    article_list.append(json.loads(
                        self.parse(link, article_id, board)))
                    time.sleep(self.DELAY_TIME)
                except:
                    pass

            if start_date:
                tmp_article_list = list(filter(lambda article: start_date < datetime.strptime(article['date'],
                                                                                              '%a %b %d %H:%M:%S %Y'),
                                               article_list))

                if len(tmp_article_list) < len(article_list):
                    if last_page == end_index:
                        # 考慮到置底文章，沒事兒
                        pass
                    else:
                        start_index = last_page
                        article_list = tmp_article_list

            if self.database_output:
                self._output_database(article_list)

            last_page -= 1
            time.sleep(self.NEXT_PAGE_DELAY_TIME)

            if self.json_output:
                prefix = arguments['json_prefix']
                self._output_json(article_list, prefix, board, last_page)


def parse_args() -> Dict[str, str]:
    parser = argparse.ArgumentParser()

    parser.add_argument('--board-name',
                        type=str,
                        required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--start-date',
                       type=str)
    group.add_argument('--index',
                       type=int,
                       metavar=('START_INDEX', 'END_INDEX'),
                       nargs=2)

    # Output
    parser.add_argument('--json-prefix',
                        type=str,
                        default='')

    # Config path
    parser.add_argument('--config-path',
                        type=str)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_args()
    crawler = PttArticleCrawler()
    crawler.go(args)


if __name__ == "__main__":
    main()
