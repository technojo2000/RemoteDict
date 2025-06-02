import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
import time
import redis
from remotedict import ExpiringRemoteDict


class TestExpiringRemoteDictServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ExpiringRemoteDict(address="127.0.0.1", port=8087, expiry_seconds=2)
        cls.server.start_thread()
        time.sleep(1)
        cls.client = redis.Redis(host='127.0.0.1', port=8087, db=0)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop_thread()
        time.sleep(0.1)

    def test_set_and_get(self):
        key = 'expirekey'
        value = 'expirevalue'
        # Set without EX, should still expire if ExpiringRemoteDict is used
        self.client.set(key, value)
        result = self.client.get(key)
        self.assertEqual(result.decode(), value)
        # Wait for expiry (default expiry_seconds in ExpiringRemoteDict is 3600, but for test, set a short expiry)
        # We'll simulate expiry by deleting and resetting with a short expiry if possible
        # But since the server uses the default expiry, we can't test expiry unless the server is constructed with a short expiry
        # So, skip the expiry assertion if the key does not expire
        time.sleep(2.1)
        expired = self.client.get(key)
        self.assertIsNone(expired, 'Key did not expire as expected. Check ExpiringRemoteDict expiry_seconds.')

    def test_delete(self):
        key1 = 'expire_del1'
        key2 = 'expire_del2'
        self.client.set(key1, 'v1')
        self.client.set(key2, 'v2')
        deleted = self.client.delete(key1, key2, 'nonexistent')
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.client.get(key1))
        self.assertIsNone(self.client.get(key2))

    def test_exists(self):
        key1 = 'expire_exist1'
        key2 = 'expire_exist2'
        self.client.set(key1, '1')
        self.client.set(key2, '2')
        exists = self.client.exists(key1, key2, 'nonexistent')
        self.assertEqual(exists, 2)
        self.client.delete(key1)
        exists = self.client.exists(key1, key2)
        self.assertEqual(exists, 1)
        self.client.delete(key2)
        exists = self.client.exists(key1, key2)
        self.assertEqual(exists, 0)

    def test_keys(self):
        key1 = 'expirekey1abc'
        key2 = 'expirekey2abc'
        key3 = 'expireotherkey'
        self.client.set(key1, 'a')
        self.client.set(key2, 'b')
        self.client.set(key3, 'c')
        keys = self.client.keys('expirekey*abc')
        keys = [k.decode() for k in keys]
        self.assertIn(key1, keys)
        self.assertIn(key2, keys)
        self.assertNotIn(key3, keys)
        self.client.delete(key1, key2, key3)

    def test_unknown_command(self):
        with self.assertRaises(redis.exceptions.ResponseError):
            self.client.execute_command('FOOBAR')

    def test_flushdb(self):
        self.client.set('a', '1')
        self.client.set('b', '2')
        self.client.set('c', '3')
        self.assertEqual(self.client.exists('a', 'b', 'c'), 3)
        self.client.flushdb()
        self.assertEqual(self.client.exists('a', 'b', 'c'), 0)

    def test_flushall(self):
        self.client.set('x', '100')
        self.client.set('y', '200')
        self.assertEqual(self.client.exists('x', 'y'), 2)
        self.client.flushall()
        self.assertEqual(self.client.exists('x', 'y'), 0)
