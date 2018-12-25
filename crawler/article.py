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

from models import (Article, ArticleHistory, ArticleIndex, Board, IpAsn,
                    PttDatabase, Push, User, UserLastRecord)
from utils import load_config, log

from .crawler_arg import add_article_arg_parser, get_base_parser


class PttArticleCrawler:

    PTT_URL = 'https://www.ptt.cc'
    PTT_Board_Format = '/bbs/{board}/index{index}.html'
    PTT_Article_Format = '/bbs/{board}/{web_id}.html'
    DELAY_TIME = 1.0
    NEXT_PAGE_DELAY_TIME = 5.0

    @log('Initialize')
    def __init__(self, arguments: Dict):

        config_path = (arguments['config_path'] or 'config.ini')

        self._init_config(config_path)
        self._init_database()

        self.board = arguments['board_name']
        self.timeout = None
        # self.timeout = float(self.article_config['Timeout'])

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0'}
        self.cookies = {'over18': '1'}

        self.start_date = arguments['start_date']
        self.from_database = arguments['database']
        if not self.from_database:
            self.start_index, self.end_index = (arguments['index'] if arguments['index']
                                                else (1, self.getLastPage(self.board, self.timeout)))
        else:
            self.start_index, self.end_index = (0, 0)
        logging.debug('Start date = %s', self.start_date)
        logging.debug('Start = %d, End = %d', self.start_index, self.end_index)
        logging.debug('From database = %s', str(self.from_database))

        self.upgrade_action = arguments['upgrade']

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

    def _output_index_to_database(self, result: List[tuple]):
        board = self.db.get(self.db_session,
                            Board,
                            {'name': self.board})
        index_list = []
        for web_id, link, index in result:
            logging.debug('web_id = %s, link = %s, index = %d, board.id = %d',
                          web_id, link, index, board.id)
            index_list.append({'web_id': web_id,
                               'board_id': board.id,
                               'index': index})
        self.db.bulk_update(self.db_session, ArticleIndex, index_list)

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
                logging.warning(
                    'push_ipdatetime %s search failed', push_ipdatetime)
                return None

        def parse_author(author):
            match = re.search(r'([\S]*)\D\((.*)\)', author)
            if match:
                return match.group(1)
            else:
                return author

        for record in result:
            author_username = parse_author(record['author'])
            author_conditon = {'username': author_username}
            author_values = {'username': author_username,
                             'login_times': 0,
                             'valid_article_count': 0}
            if not self.upgrade_action:
                article = self.db.get(self.db_session,
                                      Article,
                                      {'web_id': record['article_id']})
                if article:
                    continue

            user, _ = self.db.get_or_create(self.db_session,
                                            User,
                                            author_conditon,
                                            author_values,
                                            auto_commit=False)
            board, _ = self.db.get_or_create(self.db_session, Board,
                                             {'name': record['board']},
                                             {'name': record['board']},
                                             auto_commit=False)

            article, is_new_article = self.db.get_or_create(self.db_session, Article,
                                                            {'web_id': record['article_id']},
                                                            {'web_id': record['article_id'],
                                                                'user_id': user.id,
                                                                'board_id': board.id,
                                                                'post_datetime': datetime.strptime(record['date'],
                                                                                                   '%a %b %d %H:%M:%S %Y'),
                                                                'post_ip': record['ip']},
                                                            auto_commit=False)

            if record['ip']:
                _, _ = self.db.get_or_create(self.db_session,
                                             IpAsn,
                                             {'ip': record['ip']},
                                             {'ip': record['ip']},
                                             auto_commit=False)
            if not is_new_article:
                article.history[0].end_at = datetime.now()
                self.db_session.flush()

            history = self.db.create(self.db_session,
                                     ArticleHistory,
                                     {'article_id': article.id,
                                      'title': record['article_title'],
                                      'content': record['content'],
                                      'start_at': datetime.now(),
                                      'end_at': datetime.now()},
                                     auto_commit=False)

            # 更新到最近的文章歷史記錄推文
            push_list = []
            for (floor, message) in enumerate(record['messages']):
                push_user_condition = {'username': message['push_userid']}
                push_user_values = {'username': message['push_userid'],
                                    'login_times': 0,
                                    'valid_article_count': 0}
                push_user, _ = self.db.get_or_create(self.db_session,
                                                     User,
                                                     push_user_condition,
                                                     push_user_values,
                                                     auto_commit=False)
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
                                                 {'ip': push_ip},
                                                 auto_commit=False)

            self.db.bulk_insert(self.db_session, push_list, auto_commit=False)
            self.db_session.commit()

    def parse(self, link, article_id, board, timeout=3):
        """Ref: https://github.com/jwlin/ptt-web-crawler/blob/f8c04076004941d3f7584240c86a95a883ae16de/PttWebCrawler/crawler.py#L99"""
        resp = requests.get(url=link,
                            headers=self.headers,
                            cookies=self.cookies,
                            verify=True,
                            timeout=timeout)
        self.cookies = resp.cookies
        self.cookies['over18'] = '1'
        if resp.status_code != 200:
            return {"error": "invalid url"}
            # return json.dumps({"error": "invalid url"}, sort_keys=True, ensure_ascii=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        main_content = soup.find(id="main-content")
        metas = main_content.select('div.article-metaline')
        author = ''
        title = ''
        date = ''
        if metas:
            author = metas[0].select('span.article-meta-value')[
                0].string if metas[0].select('span.article-meta-value')[0] else author
            title = metas[1].select('span.article-meta-value')[0].string if metas[1].select(
                'span.article-meta-value')[0] else title
            date = metas[2].select('span.article-meta-value')[0].string if metas[2].select(
                'span.article-meta-value')[0] else date

            # remove meta nodes
            for meta in metas:
                meta.extract()
            for meta in main_content.select('div.article-metaline-right'):
                meta.extract()
        else:
            logging.info('metas is None in link %s', link)
            transcription = main_content.find(text=re.compile(u'※ 轉錄者:'))
            if transcription:
                # 轉錄文章
                match = re.search(
                    r'\W(\w+)\W\([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\),\W([0-9]+\/[0-9]+\/[0-9]+\W[0-9]+:[0-9]+:[0-9]+)', transcription)
                if match:
                    author = match.group(1)
                    date = datetime.strptime(
                        match.group(2), "%m/%d/%Y %H:%M:%S")
                    date = date.strftime('%a %b %d %H:%M:%S %Y')
            else:
                logging.info('Excuse me WTF!?')

        # remove and keep push nodes
        pushes = main_content.find_all('div', class_='push')
        for push in pushes:
            push.extract()

        try:
            ip = main_content.find(text=re.compile(u'※ 發信站:'))
            ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
        except:
            ip = None

        # 移除 '※ 發信站:' (starts with u'\u203b'), '◆ From:' (starts with u'\u25c6'), 空行及多餘空白
        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
        filtered = [v for v in main_content.stripped_strings if v[0]
                    not in [u'※', u'◆'] and v[:2] not in [u'--']]
        expr = re.compile(
            (r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))
        for i in range(len(filtered)):
            filtered[i] = re.sub(expr, '', filtered[i])

        filtered = [_f for _f in filtered if _f]  # remove empty strings
        # remove last line containing the url of the article
        filtered = [x for x in filtered if article_id not in x]
        content = ' '.join(filtered)
        content = re.sub(r'(\s)+', ' ', content)
        # print 'content', content

        # push messages
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            if not push.find('span', 'push-tag'):
                continue
            push_tag = push.find('span', 'push-tag').string.strip(' \t\n\r')
            push_userid = push.find(
                'span', 'push-userid').string.strip(' \t\n\r')
            # if find is None: find().strings -> list -> ' '.join; else the current way
            push_content = push.find('span', 'push-content').strings
            push_content = ' '.join(push_content)[
                1:].strip(' \t\n\r')  # remove ':'%a %b %d %H:%M:%S %Y
            push_ipdatetime = push.find(
                'span', 'push-ipdatetime').string.strip(' \t\n\r')
            messages.append({'push_tag': push_tag, 'push_userid': push_userid,
                             'push_content': push_content, 'push_ipdatetime': push_ipdatetime})
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        message_count = {'all': p+b+n, 'count': p -
                         b, 'push': p, 'boo': b, "neutral": n}

        # print 'msgs', messages
        # print 'mscounts', message_count

        # json data
        data = {
            'url': link,
            'board': board,
            'article_id': article_id,
            'article_title': title,
            'author': author,
            'date': date,
            'content': content,
            'ip': ip,
            'message_count': message_count,
            'messages': messages
        }
        # print 'original:', data
        return data
        # return json.dumps(data, sort_keys=True, ensure_ascii=False)

    def getLastPage(self, board, timeout=3):
        """Ref: https://github.com/jwlin/ptt-web-crawler/blob/f8c04076004941d3f7584240c86a95a883ae16de/PttWebCrawler/crawler.py#L189"""
        resp = requests.get(
            url='https://www.ptt.cc/bbs/' + board + '/index.html',
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

    @log()
    def crawling(self):
        if self.from_database:
            self._crawling_from_db()
        else:
            self._crawling_from_arg()

    @log()
    def _crawling_from_arg(self):
        last_page = self.end_index

        while last_page >= self.start_index:
            ptt_index_url = (self.PTT_URL +
                             self.PTT_Board_Format).format(board=self.board,
                                                           index=last_page)
            logging.debug('Processing index: %d, Url = %s',
                          last_page, ptt_index_url)

            resp = requests.get(url=ptt_index_url,
                                headers=self.headers,
                                cookies=self.cookies,
                                timeout=self.timeout)
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

            article_link_list = []
            for div in children:
                # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                if 'r-list-sep' in div['class']:
                    break
                elif 'r-ent' in div['class']:
                    try:
                        href = div.find('a')['href']
                        link = self.PTT_URL + href
                        article_id = re.sub(
                            '\.html', '', href.split('/')[-1])
                        article_link_list.append((article_id, link, last_page))
                    except Exception as e:
                        logging.exception(
                            'Processing article error, Url = %s', link)
                else:
                    continue
            self._output_index_to_database(article_link_list)

            article_list = []
            for article_id, link, _ in article_link_list:
                try:
                    logging.debug('Processing article: %s, Url = %s',
                                  article_id, link)

                    article_list.append(self.parse(link,
                                                   article_id,
                                                   self.board,
                                                   self.timeout))
                    time.sleep(self.DELAY_TIME)
                except Exception as e:
                    logging.exception(
                        'Processing article error, Url = %s', link)

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

            if self.json_output:
                self._output_json(article_list, last_page)

            last_page -= 1
            time.sleep(self.NEXT_PAGE_DELAY_TIME)

    @log()
    def _crawling_from_db(self):
        board = self.db.get(self.db_session, Board, {'name': self.board})

        exist_article_list = self.db_session \
            .query(Article.web_id) \
            .filter(Article.board_id == board.id).all()

        if self.upgrade_action:
            article_index_list = self.db_session \
                .query(ArticleIndex)\
                .filter(Article.board_id == board.id).all()
        else:
            article_index_list = self.db_session \
                .query(ArticleIndex) \
                .filter(ArticleIndex.web_id.notin_(exist_article_list)).all()

        article_list = []
        count = 0
        for article_index in article_index_list:
            link = self.PTT_URL + \
                self.PTT_Article_Format.format(board=article_index.board.name,
                                               web_id=article_index.web_id)
            logging.debug('Processing Url = %s', link)
            article_id = article_index.web_id
            article_list.append(self.parse(link,
                                           article_id,
                                           self.board,
                                           self.timeout))
            time.sleep(self.DELAY_TIME)
            count += 1
            if count == 20:
                self._output_database(article_list)
                article_list = []
                count = 0


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
