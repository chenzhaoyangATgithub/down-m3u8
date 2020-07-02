# coding: utf-8
from . import aes128


def get_parser(p_name):
    if p_name == "AES-128":
        return aes128.parser
    else:
        return default_parser


def default_parser(i, *args, **kwargs):
    return i
