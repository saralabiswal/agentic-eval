"""In-memory API state for local benchmark runs."""

from __future__ import annotations

import asyncio

from eval.core.schemas import BenchmarkReport

REPORTS: dict[str, BenchmarkReport] = {}
EVENTS: dict[str, list[dict[str, object]]] = {}
QUEUES: dict[str, asyncio.Queue[dict[str, object]]] = {}
ERRORS: dict[str, dict[str, object]] = {}
