import configparser
from typing import Dict, List


def load_config(config_path: str = 'config.ini') -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(config_path)

    return config
