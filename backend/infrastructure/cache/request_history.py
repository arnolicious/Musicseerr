"""Backward-compat shim — re-exports from infrastructure.persistence."""
from infrastructure.persistence.request_history import RequestHistoryRecord, RequestHistoryStore

__all__ = ["RequestHistoryRecord", "RequestHistoryStore"]
