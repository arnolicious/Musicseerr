import asyncio
import pytest
from core.task_registry import TaskRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    TaskRegistry.get_instance().reset()
    yield
    TaskRegistry.get_instance().reset()


def test_singleton():
    a = TaskRegistry.get_instance()
    b = TaskRegistry.get_instance()
    assert a is b


@pytest.mark.asyncio
async def test_register_and_get_all():
    registry = TaskRegistry.get_instance()
    tasks = [asyncio.create_task(asyncio.sleep(10)) for _ in range(3)]
    for i, t in enumerate(tasks):
        registry.register(f"task-{i}", t)
    assert len(registry.get_all()) == 3
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_duplicate_running_task_raises():
    registry = TaskRegistry.get_instance()
    t = asyncio.create_task(asyncio.sleep(10))
    registry.register("dup", t)
    with pytest.raises(RuntimeError, match="already running"):
        registry.register("dup", asyncio.create_task(asyncio.sleep(10)))
    t.cancel()
    await asyncio.gather(t, return_exceptions=True)


@pytest.mark.asyncio
async def test_duplicate_done_task_replaces():
    registry = TaskRegistry.get_instance()
    t1 = asyncio.create_task(asyncio.sleep(0))
    registry.register("done-test", t1)
    await t1
    await asyncio.sleep(0.05)
    t2 = asyncio.create_task(asyncio.sleep(10))
    registry.register("done-test", t2)
    assert registry.get_all()["done-test"] is t2
    t2.cancel()
    await asyncio.gather(t2, return_exceptions=True)


@pytest.mark.asyncio
async def test_unregister():
    registry = TaskRegistry.get_instance()
    t = asyncio.create_task(asyncio.sleep(10))
    registry.register("unreg", t)
    registry.unregister("unreg")
    assert len(registry.get_all()) == 0
    t.cancel()
    await asyncio.gather(t, return_exceptions=True)


@pytest.mark.asyncio
async def test_auto_unregister_on_completion():
    registry = TaskRegistry.get_instance()
    t = asyncio.create_task(asyncio.sleep(0))
    registry.register("auto-unreg", t)
    await t
    await asyncio.sleep(0.05)
    assert "auto-unreg" not in registry.get_all()


@pytest.mark.asyncio
async def test_cancel_all_cancels_tasks():
    registry = TaskRegistry.get_instance()
    tasks = [asyncio.create_task(asyncio.sleep(100)) for _ in range(5)]
    for i, t in enumerate(tasks):
        registry.register(f"cancel-{i}", t)
    await registry.cancel_all(grace_period=2.0)
    assert all(t.done() for t in tasks)


@pytest.mark.asyncio
async def test_cancel_all_with_grace_period():
    registry = TaskRegistry.get_instance()

    async def slow_cleanup():
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            await asyncio.sleep(5)

    t = asyncio.create_task(slow_cleanup())
    registry.register("slow", t)
    await registry.cancel_all(grace_period=0.5)
    assert len(registry.get_all()) == 0


@pytest.mark.asyncio
async def test_is_running():
    registry = TaskRegistry.get_instance()
    t = asyncio.create_task(asyncio.sleep(0))
    registry.register("running-check", t)
    assert registry.is_running("running-check") is True
    await t
    await asyncio.sleep(0.05)
    assert registry.is_running("running-check") is False


@pytest.mark.asyncio
async def test_reset():
    registry = TaskRegistry.get_instance()
    tasks = [asyncio.create_task(asyncio.sleep(10)) for _ in range(3)]
    for i, t in enumerate(tasks):
        registry.register(f"reset-{i}", t)
    registry.reset()
    assert len(registry.get_all()) == 0
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
