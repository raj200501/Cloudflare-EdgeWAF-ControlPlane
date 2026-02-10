from apps.edge.store import EventRecord, InMemoryStateBackend, RedisStateBackend


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.lists = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def lpush(self, key, value):
        self.lists.setdefault(key, [])
        self.lists[key].insert(0, value)

    def ltrim(self, key, start, end):
        self.lists[key] = self.lists.get(key, [])[start : end + 1]

    def lrange(self, key, start, end):
        return self.lists.get(key, [])[start : end + 1]


def make_event():
    return EventRecord(
        id="1",
        ts=1.0,
        decision="allow",
        reason="ok",
        ip="1.1.1.1",
        country="US",
        path="/a",
        method="GET",
        status_code=200,
        latency_ms=5,
        timings={"total": 5},
    )


def test_in_memory_backend_roundtrip():
    backend = InMemoryStateBackend()
    backend.put_json("a", {"x": 1})
    assert backend.get_json("a")["x"] == 1
    backend.append_event(make_event())
    assert len(backend.recent_events()) == 1


def test_redis_backend_roundtrip():
    backend = RedisStateBackend(FakeRedis(), prefix="t")
    backend.put_json("a", {"x": 2})
    assert backend.get_json("a")["x"] == 2
    backend.append_event(make_event())
    assert backend.recent_events(limit=2)[0]["id"] == "1"
