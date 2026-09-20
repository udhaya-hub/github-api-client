import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from api_client.config import get_settings
from api_client.exceptions import CacheError


def _resolve_db_path(db_path: Path | None) -> str:
    if db_path is None:
        s = get_settings()
        return str(s.cache_db_path)
    if str(db_path) == ":memory:":
        return "file::memory:?cache=shared"
    return str(db_path)


class Cache:
    def __init__(self, db_path: Path | None = None, ttl: int | None = None):
        s = get_settings()
        self.db_path = _resolve_db_path(db_path)
        self.ttl = ttl or s.cache_ttl
        self._init_db()

    def _init_db(self) -> None:
        try:
            with self._connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expires_at REAL NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
                    """
                )
                conn.commit()
        except sqlite3.Error as e:
            raise CacheError(f"Failed to initialize cache database: {e}") from e

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get(self, key: str) -> Any | None:
        try:
            with self._connection() as conn:
                row = conn.execute(
                    "SELECT value, expires_at FROM cache WHERE key = ?",
                    (key,),
                ).fetchone()

                if row is None:
                    return None

                if time.time() > row["expires_at"]:
                    self.delete(key)
                    return None

                return json.loads(row["value"])
        except (sqlite3.Error, json.JSONDecodeError) as e:
            raise CacheError(f"Cache get failed for key '{key}': {e}") from e

    def set(self, key: str, value: Any) -> None:
        try:
            expires_at = time.time() + self.ttl
            with self._connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                    (key, json.dumps(value), expires_at),
                )
                conn.commit()
        except (sqlite3.Error, TypeError) as e:
            raise CacheError(f"Cache set failed for key '{key}': {e}") from e

    def delete(self, key: str) -> None:
        try:
            with self._connection() as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
        except sqlite3.Error as e:
            raise CacheError(f"Cache delete failed for key '{key}': {e}") from e

    def clear_expired(self) -> int:
        try:
            with self._connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE expires_at < ?", (time.time(),)
                )
                conn.commit()
                return int(cursor.rowcount)
        except sqlite3.Error as e:
            raise CacheError(f"Cache clear expired failed: {e}") from e

    def clear_all(self) -> int:
        try:
            with self._connection() as conn:
                cursor = conn.execute("DELETE FROM cache")
                conn.commit()
                return int(cursor.rowcount)
        except sqlite3.Error as e:
            raise CacheError(f"Cache clear all failed: {e}") from e


_cache_instance: Cache | None = None


def get_cache() -> Cache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance
