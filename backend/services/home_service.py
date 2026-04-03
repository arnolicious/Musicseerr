"""Backward-compat shim — re-exports HomeService from services.home.facade."""
from services.home.facade import HomeService

__all__ = ["HomeService"]
