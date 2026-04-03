import pytest
from pathlib import Path
from infrastructure.queue.queue_store import QueueStore


@pytest.fixture
def store(tmp_path: Path) -> QueueStore:
    return QueueStore(db_path=tmp_path / "test_queue.db")


def test_enqueue_and_get_pending(store: QueueStore):
    store.enqueue("j1", "mbid-1")
    store.enqueue("j2", "mbid-2")
    store.enqueue("j3", "mbid-3")
    assert len(store.get_pending()) == 3


def test_dequeue_removes_job(store: QueueStore):
    store.enqueue("j1", "mbid-1")
    store.dequeue("j1")
    assert len(store.get_pending()) == 0


def test_duplicate_enqueue_ignored(store: QueueStore):
    assert store.enqueue("j1", "mbid-1") is True
    assert store.enqueue("j2", "mbid-1") is False
    assert len(store.get_pending()) == 1


def test_mark_processing(store: QueueStore):
    store.enqueue("j1", "mbid-1")
    store.mark_processing("j1")
    assert len(store.get_pending()) == 0
    assert len(store.get_all()) == 1


def test_reset_processing(store: QueueStore):
    store.enqueue("j1", "mbid-1")
    store.mark_processing("j1")
    store.reset_processing()
    assert len(store.get_pending()) == 1


def test_add_dead_letter_retryable(store: QueueStore):
    store.add_dead_letter("j1", "mbid-1", "error", retry_count=1, max_retries=3)
    retryable = store.get_retryable_dead_letters()
    assert len(retryable) == 1
    assert retryable[0]["album_mbid"] == "mbid-1"


def test_add_dead_letter_exhausted(store: QueueStore):
    store.add_dead_letter("j1", "mbid-1", "error", retry_count=3, max_retries=3)
    assert len(store.get_retryable_dead_letters()) == 0


def test_remove_dead_letter(store: QueueStore):
    store.add_dead_letter("j1", "mbid-1", "error", retry_count=1, max_retries=3)
    store.remove_dead_letter("j1")
    assert len(store.get_retryable_dead_letters()) == 0


def test_update_dead_letter_attempt(store: QueueStore):
    store.add_dead_letter("j1", "mbid-1", "error1", retry_count=1, max_retries=3)
    store.update_dead_letter_attempt("j1", "error2", retry_count=3)
    assert len(store.get_retryable_dead_letters()) == 0
    assert store.get_dead_letter_count() == 1


def test_get_dead_letter_count(store: QueueStore):
    store.add_dead_letter("j1", "mbid-1", "e1", 1, 3)
    store.add_dead_letter("j2", "mbid-2", "e2", 1, 3)
    store.add_dead_letter("j3", "mbid-3", "e3", 1, 3)
    assert store.get_dead_letter_count() == 3


def test_has_pending_mbid(store: QueueStore):
    assert store.has_pending_mbid("mbid-1") is False
    store.enqueue("j1", "mbid-1")
    assert store.has_pending_mbid("mbid-1") is True
    store.mark_processing("j1")
    assert store.has_pending_mbid("mbid-1") is False
    store.dequeue("j1")
    assert store.has_pending_mbid("mbid-1") is False


def test_enqueue_returns_bool(store: QueueStore):
    assert store.enqueue("j1", "mbid-1") is True
    assert store.enqueue("j1", "mbid-1") is False
