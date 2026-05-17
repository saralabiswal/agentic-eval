"""FastAPI application for benchmark results and live events."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eval.api.report_cleanup import cleanup_generated_reports
from eval.api.routers import benchmark, cases, config, results, sse


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Run startup maintenance before serving benchmark API traffic."""

    # Keep the Results page useful without letting generated report files grow forever.
    await asyncio.to_thread(cleanup_generated_reports, None, 3)
    yield


app = FastAPI(title="agentic-eval API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(benchmark.router)
app.include_router(results.router)
app.include_router(cases.router)
app.include_router(config.router)
app.include_router(sse.router)
