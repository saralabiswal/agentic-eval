"""Test case browsing API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from eval.benchmark import BenchmarkEngine

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("")
async def list_cases() -> list[dict[str, object]]:
    """List all YAML test cases."""

    return [case.model_dump(mode="json") for case in BenchmarkEngine().load_cases()]


@router.get("/{case_id}")
async def get_case(case_id: str) -> dict[str, object]:
    """Return one test case by ID."""

    cases = BenchmarkEngine().load_cases([case_id])
    if not cases:
        raise HTTPException(status_code=404, detail="Case not found")
    return cases[0].model_dump(mode="json")
