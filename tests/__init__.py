from pyres import ResQ, str_to_class
import os
import os.path as path
import redis
import sys
import unittest
import subprocess

CXN_STR = _cxn_str = "localhost:6345"
_proc = None


def setUp():
    # make sure redis is running
    resq = ResQ(server=_cxn_str)
    try:
        resq.redis.connect()
    except redis.ConnectionError:
        venv = os.environ.get('VIRTUAL_ENV')
        rspath = path.join(venv, 'bin', 'redis-server')
        if path.exists(rspath): # they've done a pavement or virtualenv setup
            # start redis with the test config
            global _proc
            args = [rspath, path.join(path.abspath('.'), 'tests/test-redis.conf')]
            _proc = subprocess.Popen(args)
            cxn = False
            while cxn == False:
                try:
                    resq.redis.connect()
                    cxn = True
                except redis.ConnectionError:
                    cxn = False
        else:
            raise SystemError("Redis is not running")


def tearDown():
    resq = ResQ(server=_cxn_str)
    resq.redis.flush()
    resq.redis.shutdown()


class Basic(object):
    queue = 'basic'
    
    @staticmethod
    def perform(name):
        s = "name:%s" % name
        print s
        return s


class TestProcess(object):
    queue = 'high'
    
    @staticmethod
    def perform():
        import time
        time.sleep(.5)
        return 'Done Sleeping'
        
    
class ErrorObject(object):
    queue = 'basic'
    
    @staticmethod
    def perform():
        raise Exception("Could not finish job")


class LongObject(object):
    queue = 'long_runnning'
    
    @staticmethod
    def perform(sleep_time):
        import time
        time.sleep(sleep_time)
        print 'Done Sleeping'


def test_str_to_class():
    ret = str_to_class('tests.Basic')
    assert ret


class PyResTests(unittest.TestCase):
    _cxn_str = "localhost:6345"
    def setUp(self):
        self.resq = ResQ(server=self._cxn_str)
        self.redis = self.resq.redis
        self.redis.flush(True)
    
    def tearDown(self):
        self.redis.flush(True)
        del self.redis
        del self.resq
