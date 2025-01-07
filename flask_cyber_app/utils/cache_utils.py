from threading import Lock
import time


class CacheUtils:
    _cache = {}
    _lock = Lock()

    @classmethod
    def store(cls, key, value, ttl=3600):
        """
        Store a value in the cache with an optional TTL (time-to-live).
        """
        expiration_time = time.time() + ttl
        with cls._lock:
            cls._cache[key] = {"value": value, "expires_at": expiration_time}

    @classmethod
    def retrieve(cls, key):
        """
        Retrieve a value from the cache. Returns None if the key doesn't exist or has expired.
        """
        with cls._lock:
            item = cls._cache.get(key)
            if item and item["expires_at"] > time.time():
                return item["value"]
            # Remove expired item
            cls._cache.pop(key, None)
        return None

    @classmethod
    def delete(cls, key):
        """
        Remove a key from the cache.
        """
        with cls._lock:
            cls._cache.pop(key, None)
