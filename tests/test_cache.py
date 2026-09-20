import tempfile
import time

import pytest

from api_client.cache import Cache


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name


def test_cache_set_and_get(temp_db):
    cache = Cache(db_path=temp_db, ttl=3600)
    cache.set("test_key", {"data": "value"})
    result = cache.get("test_key")
    assert result == {"data": "value"}


def test_cache_miss(temp_db):
    cache = Cache(db_path=temp_db, ttl=3600)
    result = cache.get("nonexistent")
    assert result is None


def test_cache_expiration(temp_db):
    cache = Cache(db_path=temp_db, ttl=1)
    cache.set("test_key", "value")
    assert cache.get("test_key") == "value"
    time.sleep(1.1)
    assert cache.get("test_key") is None


def test_cache_delete(temp_db):
    cache = Cache(db_path=temp_db, ttl=3600)
    cache.set("test_key", "value")
    cache.delete("test_key")
    assert cache.get("test_key") is None


def test_cache_clear_expired(temp_db):
    cache = Cache(db_path=temp_db, ttl=1)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    time.sleep(1.1)
    cleared = cache.clear_expired()
    assert cleared == 2


def test_cache_clear_all(temp_db):
    cache = Cache(db_path=temp_db, ttl=3600)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cleared = cache.clear_all()
    assert cleared == 2
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cache_complex_objects(temp_db):
    cache = Cache(db_path=temp_db, ttl=3600)
    complex_data = {
        "list": [1, 2, 3],
        "nested": {"a": "b"},
        "string": "test",
        "number": 42,
        "bool": True,
        "null": None,
    }
    cache.set("complex", complex_data)
    result = cache.get("complex")
    assert result == complex_data
