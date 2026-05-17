"""JSON benchmark report writer."""

from __future__ import annotations

import asyncio
from pathlib import Path

from eval.core.schemas import BenchmarkReport


class JsonReporter:
    """Save benchmark reports as machine-readable JSON."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or Path("reports")

    async def save(self, report: BenchmarkReport) -> Path:
        """Write a benchmark report JSON file and return its path."""

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{report.run_timestamp:%Y%m%dT%H%M%SZ}_{report.model_backend}.json"
        path = self.reports_dir / filename
        content = report.model_dump_json(indent=2)
        await asyncio.to_thread(path.write_text, content, "utf-8")
        return path
