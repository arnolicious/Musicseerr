import asyncio
import time

import pytest

from infrastructure.resilience.retry import CircuitBreaker, CircuitState


@pytest.mark.asyncio
async def test_concurrent_arecord_failure_does_not_overcount():
    cb = CircuitBreaker(failure_threshold=5, name="test-overcount")

    async def fail_once():
        await cb.arecord_failure()

    await asyncio.gather(*[fail_once() for _ in range(10)])

    assert cb.failure_count <= 10
    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_concurrent_arecord_success_transitions_half_open_to_closed():
    cb = CircuitBreaker(failure_threshold=3, success_threshold=2, name="test-success-transition")

    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.state = CircuitState.HALF_OPEN
    cb.success_count = 0

    async def succeed_once():
        await cb.arecord_success()

    await asyncio.gather(*[succeed_once() for _ in range(10)])

    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.success_count == 0


@pytest.mark.asyncio
async def test_atry_transition_open_to_half_open():
    cb = CircuitBreaker(failure_threshold=3, timeout=0.0, name="test-transition")

    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.01)
    await cb.atry_transition()

    assert cb.state == CircuitState.HALF_OPEN
    assert cb.success_count == 0


@pytest.mark.asyncio
async def test_atry_transition_noop_when_not_open():
    cb = CircuitBreaker(name="test-noop")
    assert cb.state == CircuitState.CLOSED

    await cb.atry_transition()
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_atry_transition_noop_when_timeout_not_elapsed():
    cb = CircuitBreaker(failure_threshold=3, timeout=60.0, name="test-timeout-not-elapsed")

    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN

    await cb.atry_transition()
    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_sync_methods_still_work_without_await():
    cb = CircuitBreaker(failure_threshold=3, success_threshold=1, name="test-sync-compat")

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 2

    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0

    cb.record_success()
    assert cb.failure_count == 0


@pytest.mark.asyncio
async def test_concurrent_atry_transition_only_transitions_once():
    cb = CircuitBreaker(failure_threshold=3, timeout=0.0, name="test-double-transition")

    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.01)

    transition_states = []

    async def try_transition():
        await cb.atry_transition()
        transition_states.append(cb.state)

    await asyncio.gather(*[try_transition() for _ in range(5)])

    assert cb.state == CircuitState.HALF_OPEN
    assert all(s == CircuitState.HALF_OPEN for s in transition_states)
