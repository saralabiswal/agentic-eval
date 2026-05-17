"""Full benchmark integration tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

from eval.benchmark import BenchmarkEngine


def test_full_benchmark_generates_reports_and_is_deterministic(tmp_path: Path) -> None:
    """Run all cases twice and verify deterministic mock scores and reports."""

    first = asyncio.run(BenchmarkEngine(reports_dir=tmp_path).run(backend="mock"))
    second = asyncio.run(BenchmarkEngine(reports_dir=tmp_path).run(backend="mock"))

    assert first.total_cases == 11
    assert len(first.results) == 11
    assert list(tmp_path.glob("*.html"))
    assert list(tmp_path.glob("*.json"))

    first_scores = [result.overall_score for result in first.results]
    second_scores = [result.overall_score for result in second.results]
    assert first_scores == second_scores

    for result in first.results:
        assert 0.0 <= result.faithfulness.score <= 1.0
        assert 0.0 <= result.answer_relevance.score <= 1.0
        assert 0.0 <= result.context_precision.score <= 1.0
        assert 0.0 <= result.consistency.score <= 1.0
        assert 0.0 <= result.overall_score <= 1.0
