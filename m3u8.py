# coding: utf-8

from gevent import monkey

monkey.patch_all()
from gevent.pool import Pool
import gevent
import requests
import urlparse
import os
import time
import sys
import re
from parser import parser


class Downloader:
    def __init__(self, pool_size, retry=3):
        self.pool = Pool(pool_size)
        self.session = self._get_http_session(pool_size, pool_size, retry)
        self.retry = retry
        self.dir = ''
        self.succed = {}
        self.failed = []
        self.ts_total = 0
        self.finish = 0
        self.method = ""
        self.key = ""
        self.base_url = ""
        self.m3u8_url = ""
        self.parser = parser.default_parser

    def _get_http_session(self, pool_connections, pool_maxsize, max_retries):
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize,
                                                max_retries=max_retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def read_key(self, uri):
        r = self.session.get(uri, timeout=10)
        key = ""
        if r.ok:
            key = r.content
        return key

    def get_secret_method(self, body):
        print u"获取加密方式..."
        _list = body.split('\n')
        _list = [i for i in _list if "EXT-X-KEY" in i]
        if _list:
            item = _list[0]
            result = re.findall(r'METHOD=(.*?),URI="(.*?)"', item)
            if len(result) == 0:
                return "", ""
            method, uri = re.findall(r'METHOD=(.*?),URI="(.*?)"', item)[0]
            uri = urlparse.urljoin(self.m3u8_url, uri)
            self.method = method
            self.key = self.read_key(uri)
            print u"加密方法=", method, u"key=", self.key
            self.parser = parser.get_parser(method)
        else:
            return "", ""

    def run(self, m3u8_url, dir=''):
        self.dir = dir
        self.m3u8_url = m3u8_url
        if self.dir and not os.path.isdir(self.dir):
            os.makedirs(self.dir)

        print u"读取m3u8信息中..."
        r = self.session.get(m3u8_url, timeout=10)
        if r.ok:
            body = r.content
            self.get_secret_method(body)

            if body:
                ts_list = [urlparse.urljoin(m3u8_url, n.strip()) for n in body.split('\n') if
                           n and not n.startswith("#")]
                ts_list = zip(ts_list, [n for n in xrange(len(ts_list))])
                if ts_list:
                    self.ts_total = len(ts_list)
                    print self.ts_total
                    g1 = gevent.spawn(self._join_file)
                    self._download(ts_list)
                    g1.join()
        else:
            print r.status_code

    def _download(self, ts_list):
        self.pool.map(self._worker, ts_list)
        if self.failed:
            ts_list = self.failed
            self.failed = []
            self._download(ts_list)

    def _worker(self, ts_tuple):
        url = ts_tuple[0]
        index = ts_tuple[1]
        retry = self.retry
        while retry:
            try:
                file_name = str(index) + "_" + url.split('/')[-1].split('?')[0]
                write_to = os.path.join(self.dir, file_name)
                if not os.path.exists(write_to) or os.path.getsize(write_to) == 0:
                    r = self.session.get(url, timeout=20)
                    if r.ok:
                        content = self.parser(r.content, self.key)
                        with open(os.path.join(self.dir, file_name), 'wb') as f:
                            f.write(content)
                self.succed[index] = file_name
                self.finish += 1
                sys.stdout.write("\r已经完成({} / {})                  ".format(self.finish, self.ts_total))
                sys.stdout.flush()
                return
            except:
                import traceback
                traceback.print_exc()
                retry -= 1
        print '[FAIL]%s' % url
        self.failed.append((url, index))

    def _join_file(self):
        index = 0
        outfile = ''
        i_f = open(os.path.join(self.dir, 'index.list'), 'w')
        while index < self.ts_total:
            file_name = self.succed.get(index, '')
            if file_name:
                i_f.write('file ' + file_name + '\n')
                i_f.flush()
                index += 1
            else:
                time.sleep(1)
        if outfile:
            outfile.close()


if __name__ == '__main__':
    downloader = Downloader(50)
    import sys

    try:
        m = sys.argv[1]
        p = sys.argv[2]
        downloader.run(m, p)
    except Exception, e:
        import traceback

        traceback.print_exc()
        print "down-m3u8 m3u8-url save-path"
        # downloader.run('https://c9d3.vvvvbaidu.com/hls/5167196/240.m3u8', './IBW-109/')
