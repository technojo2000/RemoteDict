import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
import time
import redis
from remotedict import PersistentRemoteDict, PersistentExpiringRemoteDict


class TestPersistentRemoteDictServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = PersistentRemoteDict(address="127.0.0.1", port=8088)
        cls.server.start_thread()
        time.sleep(1)
        cls.client = redis.Redis(host='127.0.0.1', port=8088, db=0)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop_thread()
        time.sleep(0.1)

    def test_set_and_get(self):
        key = 'persistkey'
        value = 'persistvalue'
        self.client.set(key, value)
        result = self.client.get(key)
        self.assertEqual(result.decode(), value)

    def test_delete(self):
        key1 = 'persist_del1'
        key2 = 'persist_del2'
        self.client.set(key1, 'v1')
        self.client.set(key2, 'v2')
        deleted = self.client.delete(key1, key2, 'nonexistent')
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.client.get(key1))
        self.assertIsNone(self.client.get(key2))

    def test_exists(self):
        key1 = 'persist_exist1'
        key2 = 'persist_exist2'
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
        key1 = 'persistkey1abc'
        key2 = 'persistkey2abc'
        key3 = 'persistotherkey'
        self.client.set(key1, 'a')
        self.client.set(key2, 'b')
        self.client.set(key3, 'c')
        keys = self.client.keys('persistkey*abc')
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


class TestPersistentExpiringRemoteDictServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a short expiry for testing
        cls.server = PersistentExpiringRemoteDict(address="127.0.0.1", port=8089, expiry_seconds=2)
        cls.server.start_thread()
        time.sleep(1)
        cls.client = redis.Redis(host='127.0.0.1', port=8089, db=0)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop_thread()
        time.sleep(0.1)

    def test_set_and_get(self):
        key = 'exppersistkey'
        value = 'exppersistvalue'
        self.client.set(key, value)
        result = self.client.get(key)
        self.assertEqual(result.decode(), value)
        time.sleep(2.1)
        time.sleep(2.1)
        expired = self.client.get(key)
        self.assertIsNone(expired, 'Key did not expire as expected. Check PersistentExpiringRemoteDict expiry_seconds.')

    def test_delete(self):
        key1 = 'exppersist_del1'
        key2 = 'exppersist_del2'
        self.client.set(key1, 'v1')
        self.client.set(key2, 'v2')
        deleted = self.client.delete(key1, key2, 'nonexistent')
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.client.get(key1))
        self.assertIsNone(self.client.get(key2))

    def test_exists(self):
        key1 = 'exppersist_exist1'
        key2 = 'exppersist_exist2'
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
        key1 = 'exppersistkey1abc'
        key2 = 'exppersistkey2abc'
        key3 = 'exppersistotherkey'
        self.client.set(key1, 'a')
        self.client.set(key2, 'b')
        self.client.set(key3, 'c')
        keys = self.client.keys('exppersistkey*abc')
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
