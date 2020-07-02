# coding: utf-8
from Crypto.Cipher import AES


def parser(content, key, *args, **kwargs):
    key = fill_character(key)
    cryptor = AES.new(key.encode('utf-8'), AES.MODE_CBC, b'0000000000000000')
    return cryptor.decrypt(content)


def fill_character(key):
    if len(key) < 16:
        key = key.ljust(16, '\000')
    elif len(key) > 16:
        key = key[: 16]
    return key
