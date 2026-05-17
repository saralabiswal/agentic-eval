"""Tests for the faithfulness evaluator."""

from __future__ import annotations

import pytest

from eval.evaluators._utils import load_test_case
from eval.evaluators.faithfulness import FaithfulnessEvaluator
from eval.runners.mock_runner import MockRunner


@pytest.mark.asyncio
async def test_faithfulness_score_in_range_and_passes_threshold() -> None:
    test_case = load_test_case("PR-003")
    output = "LOW risk based on no missed payments, low utilization, and checking balance."

    score = await FaithfulnessEvaluator().evaluate(test_case, output)

    assert 0.0 <= score.score <= 1.0
    assert score.passed is True


@pytest.mark.asyncio
async def test_faithfulness_detects_premium_tier_hallucination_for_pr001() -> None:
    test_case = load_test_case("PR-001")
    output = (
        "Marcus Webb is CRITICAL risk due to missed payments and utilization. "
        "He also qualifies for premium_tier handling."
    )

    score = await FaithfulnessEvaluator().evaluate(test_case, output)

    assert score.passed is False
    assert "premium_tier" in score.evidence


@pytest.mark.asyncio
async def test_pr001_mock_runner_hallucination_detected_end_to_end() -> None:
    test_case = load_test_case("PR-001")
    runner_output = await MockRunner().run(test_case)

    score = await FaithfulnessEvaluator().evaluate(test_case, runner_output.agent_output)

    assert score.passed is False
    assert "premium_tier" in score.evidence
