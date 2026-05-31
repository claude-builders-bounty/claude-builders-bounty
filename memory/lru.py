from collections import OrderedDict

class ConversationMemory:
    def __init__(self, maxsize=100):
        self._cache = OrderedDict()
        self._maxsize = maxsize
    
    def add(self, key: str, value: str):
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)
    
    def get(self, key: str) -> str | None:
        return self._cache.get(key)