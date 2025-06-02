from .expiring_remotedict import ExpiringRemoteDict
from .remotedict import RemoteDict
import json
import os

class PersistentExpiringRemoteDict(ExpiringRemoteDict):
    def __init__(self, address="127.0.0.1", port=6379, expiry_seconds=3600, filename="persistent_dict.json"):
        super().__init__(address, port, expiry_seconds)
        self._filename = filename
        self._load_from_disk()

    def _save_to_disk(self):
        data = {
            'data': self._data,
            'expiry': self._expiry
        }
        with open(self._filename, 'w') as f:
            json.dump(data, f)

    def _load_from_disk(self):
        if os.path.exists(self._filename):
            with open(self._filename, 'r') as f:
                data = json.load(f)
                self._data = data.get('data', {})
                self._expiry = data.get('expiry', {})

    def _set(self, key, value):
        super()._set(key, value)
        self._save_to_disk()

    def _del(self, keys):
        count = super()._del(keys)
        self._save_to_disk()
        return count

    def _flushdb(self):
        super()._flushdb()
        self._save_to_disk()

    def _flushall(self):
        super()._flushall()
        self._save_to_disk()

class PersistentRemoteDict(RemoteDict):
    def __init__(self, address="127.0.0.1", port=6379, filename="persistent_dict.json"):
        super().__init__(address, port)
        self._filename = filename
        self._load_from_disk()

    def _save_to_disk(self):
        data = {
            'data': self._data
        }
        with open(self._filename, 'w') as f:
            json.dump(data, f)

    def _load_from_disk(self):
        if os.path.exists(self._filename):
            with open(self._filename, 'r') as f:
                data = json.load(f)
                self._data = data.get('data', {})

    def _set(self, key, value):
        super()._set(key, value)
        self._save_to_disk()

    def _del(self, keys):
        count = super()._del(keys)
        self._save_to_disk()
        return count

    def _flushdb(self):
        super()._flushdb()
        self._save_to_disk()

    def _flushall(self):
        super()._flushall()
        self._save_to_disk()
