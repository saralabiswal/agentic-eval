"""Tests for the latency-quality tradeoff analyzer."""

from __future__ import annotations

import pytest

from eval.evaluators.latency_quality import LatencyQualityAnalyzer
from tests.unit.test_schemas import _result


@pytest.mark.asyncio
async def test_latency_quality_profiles_sorted_by_efficiency() -> None:
    fast = _result("PR-001", 0.9)
    slow = _result("PR-001", 0.95)
    slow.latency_ms = 1000
    results = {"mock": fast, "api": slow}

    report = await LatencyQualityAnalyzer().analyze(results)

    assert report.backends[0].backend == "mock"
    assert "quality per second" in report.recommendation
