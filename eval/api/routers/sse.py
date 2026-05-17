"""Server-sent event routes for live benchmark progress."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from eval.api import state

router = APIRouter(prefix="/benchmark/events", tags=["benchmark"])


@router.get("/{run_id}")
async def benchmark_events(run_id: str) -> EventSourceResponse:
    """Stream benchmark events for a run."""

    async def generator() -> AsyncIterator[dict[str, str]]:
        cursor = 0
        started_at = time.monotonic()
        next_progress_at = started_at + 5.0
        while True:
            events = state.EVENTS.get(run_id, [])
            while cursor < len(events):
                event = events[cursor]
                cursor += 1
                yield {"event": str(event["event"]), "data": json.dumps(event)}
                if event.get("event") in {"benchmark_done", "benchmark_failed"}:
                    return
            if run_id in state.REPORTS or run_id in state.ERRORS:
                return
            now = time.monotonic()
            if now >= next_progress_at:
                # Long local Ollama evaluations can be quiet for minutes; these
                # synthetic events make the live stream documentably active.
                progress = {
                    "run_id": run_id,
                    "event": "benchmark_progress",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "data": {
                        "elapsed_seconds": round(now - started_at),
                        "message": "Benchmark is still running.",
                    },
                }
                yield {"event": "benchmark_progress", "data": json.dumps(progress)}
                next_progress_at = now + 5.0
            await asyncio.sleep(0.25)

    return EventSourceResponse(generator())
