import argparse
import codecs
import json
import logging
import os
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
from utils import load_config, log

from .crawler_arg import add_article_arg_parser, get_base_parser


class PttArticleCrawler(PttWebCrawler):

    PTT_URL = 'https://www.ptt.cc'
    PTT_Board_Format = '/bbs/{board}/index{index}.html'
    DELAY_TIME = 1.0
    NEXT_PAGE_DELAY_TIME = 5.0

    @log('Initialize')
    def __init__(self, arguments: Dict):

        super().__init__(as_lib=True)

        config_path = (arguments['config_path'] or 'config.ini')

        self._init_config(config_path)
        self._init_database()

        self.board = arguments['board_name']
        self.timeout = float(self.article_config['Timeout'])

        self.start_date = arguments['start_date']
        self.start_index, self.end_index = (arguments['index'] if arguments['index']
                                            else (1, self.getLastPage(self.board, self.timeout)))
        logging.debug('Start date = %s', self.start_date)
        logging.debug('Start = %d, End = %d', self.start_index, self.end_index)

        self.json_folder = arguments['json_folder']
        self.json_prefix = arguments['json_prefix']

        if arguments['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

    def _init_config(self, config_path: str):
        self.config = load_config(config_path)
        self.article_config = self.config['PttArticle']
        self.database_config = self.config['Database']

        self.DELAY_TIME = float(self.article_config['Delaytime'])
        self.NEXT_PAGE_DELAY_TIME = float(
            self.article_config['NextPageDelaytime'])

        self.json_output = False
        self.database_output = False
        if 'Output' in self.article_config:
            if self.article_config['Output'] == 'both':
                self.json_output = True
                self.database_output = True
            elif self.article_config['Output'] == 'database':
                self.json_output = False
                self.database_output = True
            elif self.article_config['Output'] == 'json':
                self.json_output = True
                self.database_output = False

    def _init_database(self):
        self.db = PttDatabase(dbtype=self.database_config['Type'],
                              dbname=self.database_config['Name'])
        self.db_session = self.db.get_session()

    def _output_json(self, result: Dict[str, object], index):
        json_name = '{prefix}{board}_{index}.json'.format(prefix=self.json_prefix,
                                                          board=self.board,
                                                          index=index)
        json_path = os.path.join(self.json_folder, json_name)
        with codecs.open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile,
                      sort_keys=True,
                      indent=4,
                      ensure_ascii=False)

    @log('Output_Database')
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
            author_username = parse_author(record['author'])
            author_conditon = {'username': author_username}
            author_values = {'username': author_username,
                             'login_times': 0,
                             'valid_article_count': 0}
            user, _ = self.db.get_or_create(self.db_session,
                                            User,
                                            author_conditon,
                                            author_values)
            board, _ = self.db.get_or_create(self.db_session, Board,
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
            if record['ip']:
                _, _ = self.db.get_or_create(self.db_session,
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
                push_user, _ = self.db.get_or_create(self.db_session,
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
                if push_ip:
                    _, _ = self.db.get_or_create(self.db_session,
                                                 IpAsn,
                                                 {'ip': push_ip},
                                                 {'ip': push_ip})

            self.db.bulk_insert(self.db_session, push_list)

    @log()
    def crawling(self):
        last_page = self.end_index

        while last_page >= self.start_index:
            ptt_index_url = (self.PTT_URL +
                             self.PTT_Board_Format).format(board=self.board,
                                                           index=last_page)
            logging.debug('Processing index: %d, Url = %s',
                          last_page, ptt_index_url)

            resp = requests.get(url=ptt_index_url,
                                cookies={'over18': '1'},
                                timeout=self.timeout)

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
                        href = div.find('a')['href']
                        link = self.PTT_URL + href
                        article_id = re.sub(
                            '\.html', '', href.split('/')[-1])

                        logging.debug('Processing article: %s, Url = %s',
                                      article_id, link)

                        article_list.append(json.loads(
                            self.parse(link, article_id, self.board, self.timeout)))
                        time.sleep(self.DELAY_TIME)
                    else:
                        continue
                except Exception as e:
                    logging.exception('Processing article error, Url = %s',
                                      link)
                    logging.debug('Exception retry')
                    resp = requests.get(url=link,
                                        cookies={'over18': '1'},
                                        timeout=self.timeout)
                    if resp.status_code != 200:
                        resp.raise_for_status()

            len_article_list = len(article_list)
            if self.start_date:
                tmp_article_list = []
                for article in article_list:
                    try:
                        aritcle_date = datetime.strptime(article['date'],
                                                         '%a %b %d %H:%M:%S %Y')
                        if self.start_date <= aritcle_date:
                            tmp_article_list.append(article)
                    except Exception as e:
                        # 避免因為原文的日期被砍，導致無法繼續處理
                        len_article_list -= 1
                        logging.error('%s', e)
                        logging.error('article: %s , date format: %s',
                                      article['article_id'], article['date'])

                if len(tmp_article_list) < len_article_list:
                    self.start_index = last_page
                    article_list = tmp_article_list

            if self.database_output:
                self._output_database(article_list)

            last_page -= 1
            time.sleep(self.NEXT_PAGE_DELAY_TIME)

            if self.json_output:
                self._output_json(article_list, last_page)


def parse_args() -> Dict[str, str]:
    base_subparser = get_base_parser()
    parser = argparse.ArgumentParser(parents=[base_subparser])
    add_article_arg_parser(parser)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_args()
    crawler = PttArticleCrawler(args)
    crawler.crawling()


if __name__ == "__main__":
    main()
