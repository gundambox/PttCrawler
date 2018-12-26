import argparse
import datetime
import json
import os
import re
import sys
import time
from typing import Dict, List
import shutil
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from models import IpAsn, PttDatabase, User, UserLastRecord
from utils import load_config, log
import logging
from .crawler_arg import add_user_arg_parser, get_base_parser


class PttDisconnectException(WebDriverException):
    pass


class PttBrowser(object):

    ACT_DELAY_TIME = 2
    BROWSER_DEBUG_FOLDER = 'BrowserDebug'
    BROWSER_DEBUG_IMG_ROTATION = 50

    def __init__(self, executable_path: str, options: ChromeOptions, *args, **kwargs):
        self.executable_path = executable_path
        self.options = options

        self.debug_img_count = 1
        if 'debug_mode' in kwargs and kwargs['debug_mode']:
            self.debug_mode = True
            if os.path.exists(self.BROWSER_DEBUG_FOLDER):
                shutil.rmtree(self.BROWSER_DEBUG_FOLDER, ignore_errors=True)
            os.makedirs(self.BROWSER_DEBUG_FOLDER)

    def __enter__(self):
        try:
            self.browser = Chrome(executable_path=self.executable_path,
                                  chrome_options=self.options)
            self.browser.set_window_size(1920, 1080)
            return self
        except Exception as e:
            print('Please Install chrome-browser or chromium-browser.')
            raise e

    def __exit__(self, type, value, trace):
        self.browser.close()

    def connect(self, url: str):
        self.browser.get(url)
        time.sleep(self.ACT_DELAY_TIME)

    def send_keys(self, buffer: str):
        if self.debug_mode:
            image_path = os.path.join(self.BROWSER_DEBUG_FOLDER,
                                      '{count}.png'.format(count=self.debug_img_count))
            self.debug_img_count += 1
            logging.debug('Saving debug img path: %s', image_path)
            self.browser.save_screenshot(image_path)

            if self.debug_img_count > self.BROWSER_DEBUG_IMG_ROTATION:
                image_path = os.path.join(self.BROWSER_DEBUG_FOLDER,
                                          '{count}.png'.format(count=(self.debug_img_count-self.BROWSER_DEBUG_IMG_ROTATION)))
                if os.path.exists(image_path):
                    os.remove(image_path)

        logging.debug('Send buffer: %s', buffer)
        ActionChains(self.browser). \
            send_keys(buffer). \
            send_keys(Keys.ENTER). \
            perform()
        time.sleep(self.ACT_DELAY_TIME)
        if self._is_lose_connect():
            raise PttDisconnectException()
        return self

    def get_buffer(self) -> str:
        main_div = self.browser.find_element_by_xpath(
            "//div[@id='mainContainer']")
        return main_div.text

    def _is_lose_connect(self) -> bool:
        alert_div = self.browser.find_element_by_xpath(
            "//div[@id='reactAlert']")
        if alert_div and u'你斷線了' in alert_div.text:
            logging.error('Lose connection!?')
            return True
        else:
            return False


class PttUserCrawler(object):
    PTT_WEB_URL = 'http://term.ptt.cc/'

    def __init__(self, arguments: Dict):
        self.db_input = arguments['database'] or False
        self.id_list = ('' if self.db_input else arguments['id'])

        config_path = (arguments['config_path'] or 'config.ini')

        self._init_config(config_path)
        self._init_database()
        self._init_browser()

        self.ptt_browser_buffer_logger = logging.getLogger(__name__ + '.log')

        self.json_prefix = arguments['json_prefix']
        self.debug_mode = arguments['debug_mode']
        if arguments['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

    def _init_config(self, config_path: str):
        self.config = load_config(config_path)
        if self.config['PttUser']['Output'] == 'both':
            self.json_output = True
            self.database_output = True
        elif self.config['PttUser']['Output'] == 'database':
            self.json_output = False
            self.database_output = True
        elif self.config['PttUser']['Output'] == 'json':
            self.json_output = True
            self.database_output = False
        else:
            self.json_output = False
            self.database_output = False

    def _init_database(self):
        self.db = PttDatabase(dbtype=self.config['Database']['Type'],
                              dbname=self.config['Database']['Name'])
        self.db_session = self.db.get_session()

    def _init_browser(self):
        if sys.platform.startswith('linux'):
            platform = 'linux'
            exe_filename = 'chromedriver'
        elif sys.platform.startswith('win'):
            platform = 'windows'
            exe_filename = 'chromedriver.exe'
        else:
            platform = 'mac'
            exe_filename = 'chromedriver'

        self.webdriver_path = os.path.join(self.config['PttUser']['WebdriverFolder'],
                                           platform,
                                           exe_filename)
        self.chrome_options = ChromeOptions()
        self.chrome_options.add_argument('--headless')

    def _get_id_list(self) -> List[str]:
        if self.db_input:
            return list(map(lambda user: user.username,
                            self.db_session.query(User).order_by(User.login_times, User.id).all()))
        else:
            return self.id_list.split(',')

    def _output_json(self, result: Dict[str, object], count):
        json_path = '{prefix}user_{count}.json'.format(prefix=self.json_prefix,
                                                       count=count)
        with open(json_path, 'w') as jsonfile:
            json.dump(result, jsonfile,
                      sort_keys=True,
                      indent=4)

    @log('Output_Database')
    def _output_database(self, result: List[Dict[str, object]]):
        for record in result:
            user, is_new_user = self.db.get_or_create(self.db_session,
                                                      User,
                                                      {'username': record['username']},
                                                      {'username': record['username'],
                                                          'login_times': int(record['login_times']),
                                                          'valid_article_count': int(record['valid_article_count'])})
            if not is_new_user:
                user.login_times = int(record['login_times'])
                user.valid_article_count = int(record['valid_article_count'])
                self.db_session.commit()

            last_login_datetime = datetime.datetime.strptime(record['last_login_datetime'],
                                                             '%m/%d/%Y %H:%M:%S %a')
            last_record = UserLastRecord(last_login_datetime=last_login_datetime,
                                         last_login_ip=record['last_login_ip'])
            last_record.user_id = user.id
            if record['last_login_ip']:
                _, _ = self.db.get_or_create(self.db_session,
                                             IpAsn,
                                             {'ip': record['last_login_ip']},
                                             {'ip': record['last_login_ip'],
                                              'asn': None,
                                              'asn_cidr': None,
                                              'asn_country_code': None,
                                              'asn_date': None,
                                              'asn_description': None,
                                              'asn_raw': None,
                                              'asn_registry': None})

            self.db_session.add(last_record)
            self.db_session.commit()

    def _output(self, result: Dict[str, object], count):
        if self.json_output:
            self._output_json(result, count)
        if self.database_output:
            self._output_database(result)

    def _login_ptt(self, browser, userid, userpwd):
        browser.connect(self.PTT_WEB_URL)
        # Ptt login
        browser.send_keys(userid)
        browser.send_keys(userpwd)

        # 踢掉重複登入 或 刪除密碼嘗試錯誤記錄
        buffer = browser.get_buffer()
        while u"主功能表" not in buffer:
            browser.send_keys('')
            buffer = browser.get_buffer()

    @log()
    def crawling(self):

        delaytime = float(self.config['PttUser']['Delaytime'])
        userid = self.config['PttUser']['UserId']
        userpwd = self.config['PttUser']['UserPwd']

        id_list = self._get_id_list()

        crawler_result = []

        with PttBrowser(self.webdriver_path, self.chrome_options, debug_mode=self.debug_mode) as browser:

            browser.ACT_DELAY_TIME = delaytime

            self._login_ptt(browser, userid, userpwd)

            # 轉到 Talk -> Query
            browser.send_keys('T')

            id_queue = id_list.copy()
            count = 1
            err_count = 0
            while len(id_queue) > 0:
                for user_id in id_list:
                    try:
                        browser.send_keys('Q').send_keys(user_id)
                        buffer = browser.get_buffer()

                        self.ptt_browser_buffer_logger.debug('Buffer:\n%s',
                                                             buffer)

                        pattern = r"[\w\W]*《登入次數》(\d*)\D*次\D*《有效文章》\D*(\d*)[\w\W]*《上次上站》\D*([\d]{1,2}\/[\d]{1,2}\/[\d]{4}\W*[\d]{1,2}:\W*[\d]{1,2}:\W*[\d]{1,2}\W*\w*)\D*《上次故鄉》([\d.]*)"
                        pat = re.compile(pattern)
                        search_result = pat.match(buffer)

                        if search_result:
                            login_times = search_result.group(1)
                            valid_article_count = search_result.group(2)
                            last_login_datetime = search_result.group(3)
                            last_login_ip = search_result.group(4)

                            crawler_result.append({'username': user_id,
                                                   'login_times': login_times,
                                                   'valid_article_count': valid_article_count,
                                                   'last_login_datetime': last_login_datetime,
                                                   'last_login_ip': last_login_ip})

                            if len(crawler_result) % 100 == 0:
                                self._output(crawler_result, count)
                                count += 1
                                crawler_result = []
                        else:
                            logging.error('User "%s" has error', user_id)
                            self.ptt_browser_buffer_logger.error('Buffer:\n%s',
                                                                 buffer)

                        browser.send_keys('')
                        id_queue.remove(user_id)
                    except KeyboardInterrupt:
                        id_queue = []
                        break
                    except PttDisconnectException as e:
                        err_count += 1
                        if err_count == 3:
                            raise e

                        browser.send_keys('')
                        self._login_ptt(browser, userid, userpwd)
                        browser.send_keys('T')
                        continue

                self._output(crawler_result, count)
                count += 1


def parse_args() -> Dict[str, str]:
    base_subparser = get_base_parser()
    parser = argparse.ArgumentParser(parents=[base_subparser])
    add_user_arg_parser(parser)

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_args()
    crawler = PttUserCrawler(args)
    crawler.crawling()


if __name__ == "__main__":
    main()
