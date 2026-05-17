"""Benchmark result API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from eval.api import state
from eval.api.report_store import ReportStore, report_summary_row

router = APIRouter(prefix="/results", tags=["results"])


@router.get("")
async def list_results() -> list[dict[str, object]]:
    """List completed benchmark reports."""

    return [
        report_summary_row(report)
        for report in ReportStore().list_reports(state.REPORTS)
    ]


@router.get("/{run_id}")
async def get_result(run_id: str) -> dict[str, object]:
    """Return a completed benchmark report by run ID."""

    report = ReportStore().get_report(run_id, state.REPORTS)
    if report is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return report.model_dump(mode="json")
