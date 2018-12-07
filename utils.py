import argparse
import configparser
import inspect
import logging
from datetime import datetime
from typing import Dict, List


def _get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    # handle special descriptor objects
    return getattr(meth, '__objclass__', None)


def log(func_alias: str = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = '{cls}.{func}'.format(cls=_get_class_that_defined_method(func).__name__,
                                              func=(func_alias or func.__name__))
            logging.info('Start: %s', func_name)
            try:
                result = func(*args, **kwargs)
                logging.info('Finished: %s', func_name)
                return result
            except Exception as e:
                logging.info('Aborted: %s', func_name)
                logging.exception('There was an exception in %s', func_name)
        return wrapper
    return decorator


def valid_datetime_type(arg_datetime_str):
    try:
        return datetime.strptime(arg_datetime_str, "%Y-%m-%d %H:%M")
    except ValueError as e1:
        msg = "Given Datetime ({0}) not valid! Expected format, 'YYYY-MM-DD HH:mm'!".format(
            arg_datetime_str)
        raise argparse.ArgumentTypeError(msg)


def valid_date_type(arg_date_str):
    try:
        return datetime.strptime(arg_date_str, "%Y-%m-%d")
    except ValueError as e1:
        msg = "Given Datetime ({0}) not valid! Expected format, 'YYYY-MM-DD'!".format(
            arg_date_str)
        raise argparse.ArgumentTypeError(msg)


def load_config(config_path: str = 'config.ini') -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(config_path)

    return config
