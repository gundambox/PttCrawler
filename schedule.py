import os
import argparse
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List

from crontab import CronTab

from utils import load_config, valid_datetime_type


class ScheduleAction(Enum):
    update = 1
    remove = 2

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return ScheduleAction[s]
        except KeyError:
            raise ValueError()


class CrawlerModule(Enum):
    article = 1
    asn = 2
    user = 3

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return CrawlerModule[s]
        except KeyError:
            raise ValueError()


class Platform(Enum):
    windows = 1
    linux = 2
    mac = 3


class ScheduleHelper(object):

    def __init__(self):
        if sys.platform.startswith('linux'):
            self.platform = Platform['linux']
        elif sys.platform.startswith('win'):
            self.platform = Platform['windows']
        else:
            self.platform = Platform['mac']

    def _init_config(self, arguments: Dict):
        config_path = (arguments['config_path']
                       if arguments['config_path']
                       else 'config.ini')

        self.config = load_config(config_path)

    def go(self, arguments: Dict):
        self._init_config(arguments)
        action = ScheduleAction.from_string(arguments['action'])

        if self.platform == Platform.linux:
            cron = CronTab(user=True)
            cron.env['PATH'] = os.environ['PATH'] + ':' + os.getcwd()
            crawler_module = arguments['crawler_module']
            is_venv = arguments['virtualenv']
            jobs = list(cron.find_command(str(crawler_module)))

            cwd = os.getcwd()
            wrapper_path = os.path.join(cwd, 'env_wrapper.sh')

            module_command = '{wrapper_path} "{cwd}" "{env}" -m crawler {module} --database >/dev/null 2>&1'.format(
                wrapper_path=wrapper_path,
                cwd=cwd,
                env=is_venv,
                module=crawler_module)
            print(module_command)
            return
            if len(jobs) > 0:
                job = jobs[0]
                job.set_command(module_command)
            else:
                job = cron.new(command=module_command)

            if action == ScheduleAction.update:

                start_datetime = arguments['start_datetime']
                cycle_time = int(arguments['cycle_time'])

                job.minute.on(start_datetime.minute)
                job.hour.on(start_datetime.hour)
                job.dom.every(cycle_time)
                job.enable()
                print(job)
            elif action == ScheduleAction.remove:
                cron.remove(job)
            cron.write()
        elif self.platform == Platform.windows:
            raise NotImplementedError()
        elif self.platform == Platform.mac:
            raise NotImplementedError()


def parse_argument():
    base_subparser = argparse.ArgumentParser(add_help=False)
    base_subparser.add_argument('--verbose',
                                action='store_true',
                                help='Show more debug messages.')
    base_subparser.add_argument('--config-path',
                                type=str,
                                help='Config ini file path.')
    base_subparser.add_argument('--virtualenv',
                                metavar='VIRTUALENV_PATH',
                                type=str,
                                default='')

    parser = argparse.ArgumentParser(parents=[base_subparser])

    subparsers = parser.add_subparsers(dest='action',
                                       help='cmd help')
    subparsers.required = True

    update_subparser = subparsers.add_parser('update')
    update_subparser.add_argument(dest='crawler_module',
                                  type=CrawlerModule.from_string,
                                  choices=list(CrawlerModule))
    update_subparser.add_argument('-c', '--cycle-time',
                                  dest='cycle_time',
                                  type=int,
                                  required=True)
    update_subparser.add_argument('-s', '--start-datetime',
                                  dest='start_datetime',
                                  type=valid_datetime_type,
                                  default=datetime.now()+timedelta(minutes=1),
                                  help='start datetime in format "YYYY-MM-DD HH:mm"')

    remove_subparser = subparsers.add_parser('remove')
    remove_subparser.add_argument(dest='crawler_module',
                                  type=CrawlerModule.from_string,
                                  choices=list(CrawlerModule))

    args = parser.parse_args()
    arguments = vars(args)
    return arguments


def main():
    args = parse_argument()
    helper = ScheduleHelper()
    helper.go(args)


if __name__ == "__main__":
    main()
