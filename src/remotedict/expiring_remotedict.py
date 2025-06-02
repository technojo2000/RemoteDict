from .remotedict import RemoteDict
import time

class ExpiringRemoteDict(RemoteDict):
    def __init__(self, address="127.0.0.1", port=6379, expiry_seconds=3600):
        super().__init__(address, port)
        self._expiry_seconds = expiry_seconds # Default expiry time in seconds
        self._expiry = {}  # key: expiry_timestamp

    def _set(self, key, value):
        super()._set(key, value)
        if self._expiry_seconds == 0:
            self._expiry[key] = None  # None means no expiry
        else:
            self._expiry[key] = time.time() + self._expiry_seconds

    def _get(self, key):
        now = time.time()
        expiry = self._expiry.get(key)
        if expiry is not None and expiry is not None and now > expiry:
            # Expired, remove
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return None
        return super()._get(key)

    def _del(self, keys):
        count = super()._del(keys)
        for key in keys:
            self._expiry.pop(key, None)
        return count

    def _flushdb(self):
        super()._flushdb()
        self._expiry.clear()

    def _flushall(self):
        super()._flushall()
        self._expiry.clear()

    def _keys(self, pattern):
        # Only return non-expired keys
        now = time.time()
        valid_keys = [k for k in self._data.keys() if (self._expiry.get(k) is None or self._expiry.get(k, 0) > now)]
        import fnmatch
        return [k for k in valid_keys if fnmatch.fnmatch(k, pattern)]
