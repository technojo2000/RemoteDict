import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
import asyncio
import time
import threading
import redis
from remotedict import RemoteDict


class TestRemoteDictServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the custom server in a background thread
        cls.server = RemoteDict(address="127.0.0.1", port=8085)
        cls.loop = asyncio.new_event_loop()
        cls.server_thread = threading.Thread(target=cls._run_server, daemon=True)
        cls.server_thread.start()
        time.sleep(1)  # Give server time to start
        cls.client = redis.Redis(host='127.0.0.1', port=8085, db=0)

    @classmethod
    def tearDownClass(cls):
        # Stop the server cleanly and close the event loop
        async def shutdown():
            await cls.server.stop()
        try:
            # Schedule shutdown on the event loop
            future = asyncio.run_coroutine_threadsafe(shutdown(), cls.loop)
            future.result(timeout=5)
            # Give the server a moment to close all connections
            time.sleep(0.1)
            cls.loop.call_soon_threadsafe(cls.loop.stop)
            cls.server_thread.join(timeout=2)
        except Exception:
            pass
        finally:
            # Cancel all pending tasks before closing the loop
            pending = asyncio.all_tasks(loop=cls.loop)
            for task in pending:
                task.cancel()
            try:
                cls.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            cls.loop.close()

    @classmethod
    def _run_server(cls):
        asyncio.set_event_loop(cls.loop)
        cls.loop.run_until_complete(cls.server.start())
        cls.loop.run_forever()

    def test_set_and_get(self):
        key = 'testkey'
        value = 'testvalue'
        self.client.set(key, value)
        result = self.client.get(key)
        self.assertEqual(result.decode(), value)

    def test_unknown_command(self):
        # Send a truly unknown command and expect a ResponseError
        with self.assertRaises(redis.exceptions.ResponseError):
            self.client.execute_command('FOOBAR')

    def test_delete(self):
        key1 = 'todelete1'
        key2 = 'todelete2'
        self.client.set(key1, 'somevalue1')
        self.client.set(key2, 'somevalue2')
        # DEL returns number of keys deleted
        deleted = self.client.delete(key1, key2, 'nonexistent')
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.client.get(key1))
        self.assertIsNone(self.client.get(key2))

    def test_exists(self):
        key1 = 'existkey1'
        key2 = 'existkey2'
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
        key1 = 'key1abc'
        key2 = 'key2abc'
        key3 = 'otherkey'
        self.client.set(key1, 'a')
        self.client.set(key2, 'b')
        self.client.set(key3, 'c')
        keys = self.client.keys('key*abc')
        keys = [k.decode() for k in keys]
        self.assertIn(key1, keys)
        self.assertIn(key2, keys)
        self.assertNotIn(key3, keys)
        self.client.delete(key1, key2, key3)

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


class TestRemoteDictServerThreaded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the custom server using the threaded method
        cls.server = RemoteDict(address="127.0.0.1", port=8086)
        cls.server.start_thread()
        time.sleep(1)  # Give server time to start
        cls.client = redis.Redis(host='127.0.0.1', port=8086, db=0)

    @classmethod
    def tearDownClass(cls):
        # Stop the server using the threaded stop method
        cls.server.stop_thread()
        time.sleep(0.1)

    def test_set_and_get(self):
        key = 'threadedkey'
        value = 'threadedvalue'
        self.client.set(key, value)
        result = self.client.get(key)
        self.assertEqual(result.decode(), value)

    def test_delete(self):
        key1 = 'threaded_del1'
        key2 = 'threaded_del2'
        self.client.set(key1, 'v1')
        self.client.set(key2, 'v2')
        deleted = self.client.delete(key1, key2, 'nonexistent')
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.client.get(key1))
        self.assertIsNone(self.client.get(key2))

    def test_exists(self):
        key1 = 'threaded_exist1'
        key2 = 'threaded_exist2'
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
        key1 = 'threadedkey1abc'
        key2 = 'threadedkey2abc'
        key3 = 'threadedotherkey'
        self.client.set(key1, 'a')
        self.client.set(key2, 'b')
        self.client.set(key3, 'c')
        keys = self.client.keys('threadedkey*abc')
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
