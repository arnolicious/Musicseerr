"""Backward-compatible shim — re-exports ``DiscoverService`` from its new home.

All consumers that ``from services.discover_service import DiscoverService``
continue to work without changes.
"""

from services.discover.facade import DiscoverService  # noqa: F401
