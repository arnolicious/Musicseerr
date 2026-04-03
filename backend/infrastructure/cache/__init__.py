"""Ephemeral caching infrastructure — all data here can be cleared without data loss.

For durable storage, see ``infrastructure.persistence``.
"""

from infrastructure.cache.memory_cache import CacheInterface, InMemoryCache
from infrastructure.cache.disk_cache import DiskMetadataCache
from infrastructure.cache.protocol import CacheProtocol

__all__ = [
    "CacheInterface",
    "CacheProtocol",
    "InMemoryCache",
    "DiskMetadataCache",
]