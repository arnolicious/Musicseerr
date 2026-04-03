"""Backward-compat shim — re-exports LibraryPrecacheService from services.precache.orchestrator."""
from services.precache.orchestrator import LibraryPrecacheService

__all__ = ["LibraryPrecacheService"]
