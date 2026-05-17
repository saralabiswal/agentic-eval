"""Benchmark execution API routes."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from eval.api import state
from eval.benchmark import SUPPORTED_BACKENDS, BenchmarkEngine
from eval.core.runtime_config import runtime_config

router = APIRouter(prefix="/benchmark", tags=["benchmark"])
logger = structlog.get_logger(__name__)


class BenchmarkRunRequest(BaseModel):
    """Request body for starting a benchmark run."""

    backend: str | None = None
    cases: list[str] | None = None


@router.post("/run")
async def run_benchmark(
    request: BenchmarkRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Start a benchmark run in the background and return immediately."""

    backend = request.backend or runtime_config.get().sut_backend
    if backend not in SUPPORTED_BACKENDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported backend '{backend}'. Expected one of: api, mock, ollama.",
        )

    run_id = f"run_{uuid4().hex[:12]}"
    state.EVENTS[run_id] = []
    state.QUEUES[run_id] = asyncio.Queue()
    state.ERRORS.pop(run_id, None)
    background_tasks.add_task(_run_background, run_id, request, backend)
    return {"run_id": run_id}


@router.get("/{run_id}")
async def get_benchmark(run_id: str) -> dict[str, object]:
    """Return benchmark status or a completed report."""

    report = state.REPORTS.get(run_id)
    if report is None:
        error = state.ERRORS.get(run_id)
        if error is not None:
            return {"run_id": run_id, "status": "failed", "error": error}
        return {"run_id": run_id, "status": "running"}
    return report.model_dump(mode="json")


async def _run_background(run_id: str, request: BenchmarkRunRequest, backend: str) -> None:
    async def sink(event: dict[str, object]) -> None:
        event["run_id"] = run_id
        state.EVENTS.setdefault(run_id, []).append(event)
        await state.QUEUES.setdefault(run_id, asyncio.Queue()).put(event)

    try:
        report = await BenchmarkEngine(event_sink=sink).run(
            cases=request.cases,
            backend=backend,
            run_id=run_id,
        )
    except Exception as exc:
        logger.exception("benchmark_background_failed", run_id=run_id, backend=backend)
        error: dict[str, object] = {
            "message": str(exc) or exc.__class__.__name__,
            "type": exc.__class__.__name__,
        }
        state.ERRORS[run_id] = error
        event: dict[str, object] = {
            "run_id": run_id,
            "event": "benchmark_failed",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": error,
        }
        state.EVENTS.setdefault(run_id, []).append(event)
        await state.QUEUES.setdefault(run_id, asyncio.Queue()).put(event)
        return
    state.REPORTS[run_id] = report
