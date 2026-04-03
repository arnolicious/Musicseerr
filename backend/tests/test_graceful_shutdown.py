import asyncio
import pytest
from core.task_registry import TaskRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    TaskRegistry.get_instance().reset()
    yield
    TaskRegistry.get_instance().reset()


@pytest.mark.asyncio
async def test_cancel_all_stops_long_running_tasks():
    registry = TaskRegistry.get_instance()
    tasks = [asyncio.create_task(asyncio.sleep(1000)) for _ in range(5)]
    for i, t in enumerate(tasks):
        registry.register(f"long-{i}", t)
    await registry.cancel_all(grace_period=2.0)
    assert all(t.done() for t in tasks)


@pytest.mark.asyncio
async def test_cancel_all_respects_grace_period():
    registry = TaskRegistry.get_instance()

    async def stubborn_task():
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            await asyncio.sleep(10)

    t = asyncio.create_task(stubborn_task())
    registry.register("stubborn", t)
    await registry.cancel_all(grace_period=0.5)
    assert len(registry.get_all()) == 0


@pytest.mark.asyncio
async def test_shutdown_with_empty_registry():
    registry = TaskRegistry.get_instance()
    await registry.cancel_all(grace_period=1.0)
    assert len(registry.get_all()) == 0


@pytest.mark.asyncio
async def test_shutdown_with_already_done_tasks():
    registry = TaskRegistry.get_instance()
    t = asyncio.create_task(asyncio.sleep(0))
    registry.register("already-done", t)
    await t
    await asyncio.sleep(0.05)
    await registry.cancel_all(grace_period=1.0)
    assert len(registry.get_all()) == 0
