"""Tests for the context precision evaluator."""

from __future__ import annotations

import pytest

from eval.evaluators._utils import load_test_case
from eval.evaluators.context_precision import ContextPrecisionEvaluator


@pytest.mark.asyncio
async def test_context_precision_score_in_range() -> None:
    test_case = load_test_case("PR-001")
    output = "KB-HARD-001 and KB-PAY-007 support hardship and critical payment risk."

    score = await ContextPrecisionEvaluator().evaluate(test_case, output)

    assert 0.0 <= score.score <= 1.0
    assert score.threshold == test_case.evaluation_criteria.context_precision_threshold


@pytest.mark.asyncio
async def test_context_precision_threshold_bool() -> None:
    test_case = load_test_case("PR-001")
    output = "KB-HARD-001 supports hardship eligibility."

    score = await ContextPrecisionEvaluator().evaluate(test_case, output)

    assert score.passed is (score.score >= score.threshold)
