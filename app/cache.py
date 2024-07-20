from typing import List, Optional, OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.cache: OrderedDict[str, List[str]] = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[List[str]]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: List[str]) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
