from collections import OrderedDict
import threading


class LRUCache:
    def __init__(self, capacity=5000):
        self._lock = threading.Lock()
        self._data = OrderedDict()
        self._capacity = capacity

    def __contains__(self, key):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                return True
            return False

    def add(self, key):
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
            else:
                self._data[key] = True
                if len(self._data) > self._capacity:
                    self._data.popitem(last=False)

    @property
    def size(self):
        with self._lock:
            return len(self._data)


class TargetQueue:
    PORT_PRIORITY = {
        443: 5,
        80: 4,
        8443: 3,
        8080: 2,
        3000: 2,
        5000: 2,
        8888: 2,
        9090: 1,
        4443: 1,
        8000: 1,
        9000: 1,
    }

    def __init__(self, min_priority=0, lru_capacity=5000):
        self._queue = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._lru = LRUCache(capacity=lru_capacity)
        self._min_priority = min_priority
        self._closed = False

    def add(self, host, port):
        clean_port = int(str(port).split("/")[0])
        priority = self.PORT_PRIORITY.get(clean_port, 0)

        if priority < self._min_priority:
            return

        key = f"{host}:{clean_port}"
        if key in self._lru:
            return

        self._lru.add(key)

        with self._lock:
            import heapq
            heapq.heappush(self._queue, (-priority, key, host, str(clean_port)))
            self._not_empty.notify()

    def add_many(self, targets):
        for host, port in targets:
            self.add(host, port)

    def get(self, timeout=None):
        import heapq
        with self._lock:
            if not self._queue and not self._closed:
                if not self._not_empty.wait(timeout=timeout):
                    return None
            if not self._queue or self._closed:
                return None
            neg_prio, key, host, port = heapq.heappop(self._queue)
            return (host, port)

    def close(self):
        with self._lock:
            self._closed = True
            self._not_empty.notify_all()

    @property
    def size(self):
        with self._lock:
            return len(self._queue)

    @property
    def processed_count(self):
        return self._lru.size
