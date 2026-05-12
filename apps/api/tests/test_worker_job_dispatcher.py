"""Unit tests for app/worker/job_dispatcher.py.

Tests cover: enqueue, custom job registration, history recording, failure
recording, unknown-job guard, and the history deque size cap.
"""

import asyncio
import pytest

from app.worker.job_dispatcher import (
    enqueue_job,
    register_job,
    get_job_history,
    _job_history,
    _HISTORY_MAX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _drain() -> None:
    """Yield control so asyncio.create_task callbacks can execute."""
    for _ in range(10):
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enqueue_unknown_job_returns_none() -> None:
    """Enqueueing a name not in the registry must return None immediately."""
    result = await enqueue_job("nonexistent_job_xyz")
    assert result is None


@pytest.mark.asyncio
async def test_enqueue_known_job_returns_job_id() -> None:
    """Enqueueing a registered job returns a non-empty string job ID."""
    executed: list[str] = []

    async def _noop(**kwargs):
        executed.append("ran")

    register_job("_test_noop", _noop)
    job_id = await enqueue_job("_test_noop")

    assert job_id is not None
    assert len(job_id) > 0

    await _drain()
    assert executed == ["ran"]


@pytest.mark.asyncio
async def test_history_records_enqueued_then_running_then_completed() -> None:
    """A successful job produces enqueued → running → completed entries."""
    _job_history.clear()

    async def _quick(**kwargs):
        pass

    register_job("_test_quick", _quick)
    job_id = await enqueue_job("_test_quick")
    await _drain()

    statuses = [e["status"] for e in _job_history if e["job_id"] == job_id]
    assert "enqueued" in statuses
    assert "running" in statuses
    assert "completed" in statuses


@pytest.mark.asyncio
async def test_history_records_failed_status_on_exception() -> None:
    """A job that raises an exception is recorded with status='failed'."""
    _job_history.clear()

    async def _boom(**kwargs):
        raise ValueError("deliberate failure")

    register_job("_test_boom", _boom)
    job_id = await enqueue_job("_test_boom")
    await _drain()

    failure_entries = [
        e for e in _job_history if e["job_id"] == job_id and e["status"] == "failed"
    ]
    assert len(failure_entries) == 1
    assert "deliberate failure" in failure_entries[0]["error"]


@pytest.mark.asyncio
async def test_history_passes_kwargs_to_job() -> None:
    """kwargs passed to enqueue_job are forwarded to the job function."""
    received: dict = {}

    async def _capture(**kwargs):
        received.update(kwargs)

    register_job("_test_kwargs", _capture)
    await enqueue_job("_test_kwargs", project_id="p-123", user="alice")
    await _drain()

    assert received["project_id"] == "p-123"
    assert received["user"] == "alice"


@pytest.mark.asyncio
async def test_get_job_history_newest_first() -> None:
    """get_job_history() returns a list with the most-recent entry first."""
    _job_history.clear()

    async def _noop2(**kwargs):
        pass

    register_job("_test_order", _noop2)
    await enqueue_job("_test_order")
    await enqueue_job("_test_order")
    await _drain()

    history = get_job_history()
    assert len(history) >= 2
    # Most-recent entry must have a recorded_at >= the second entry
    assert history[0]["recorded_at"] >= history[1]["recorded_at"]


@pytest.mark.asyncio
async def test_history_buffer_does_not_exceed_max_size() -> None:
    """The deque never grows beyond _HISTORY_MAX entries."""
    _job_history.clear()

    async def _tiny(**kwargs):
        pass

    register_job("_test_overflow", _tiny)

    # Enqueue 10 more than the cap; each job records 3 entries (enqueued/running/completed)
    over = _HISTORY_MAX // 3 + 10
    for _ in range(over):
        await enqueue_job("_test_overflow")

    await _drain()

    assert len(_job_history) <= _HISTORY_MAX


@pytest.mark.asyncio
async def test_multiple_jobs_tracked_independently() -> None:
    """History entries from concurrent jobs don't bleed into each other."""
    _job_history.clear()
    results: list[str] = []

    async def _job_a(**kwargs):
        results.append("a")

    async def _job_b(**kwargs):
        results.append("b")

    register_job("_test_multi_a", _job_a)
    register_job("_test_multi_b", _job_b)

    id_a = await enqueue_job("_test_multi_a")
    id_b = await enqueue_job("_test_multi_b")
    await _drain()

    assert id_a != id_b
    assert "a" in results
    assert "b" in results

    ids_in_history = {e["job_id"] for e in _job_history}
    assert id_a in ids_in_history
    assert id_b in ids_in_history
