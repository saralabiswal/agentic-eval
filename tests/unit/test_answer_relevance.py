"""Tests for the answer relevance evaluator."""

from __future__ import annotations

import pytest

from eval.evaluators._utils import load_test_case
from eval.evaluators.answer_relevance import AnswerRelevanceEvaluator
from eval.evaluators.embeddings import (
    DeterministicEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from eval.runners.mock_runner import MockRunner


@pytest.mark.asyncio
async def test_answer_relevance_score_in_range_and_passes_threshold() -> None:
    test_case = load_test_case("BD-001")
    output = test_case.input.scenario_context

    score = await AnswerRelevanceEvaluator(
        DeterministicEmbeddingProvider()
    ).evaluate(test_case, output)

    assert 0.0 <= score.score <= 1.0
    assert score.passed is True


@pytest.mark.asyncio
async def test_answer_relevance_fails_for_unrelated_output() -> None:
    test_case = load_test_case("BD-001")

    score = await AnswerRelevanceEvaluator(
        DeterministicEmbeddingProvider()
    ).evaluate(test_case, "Discuss mortgage refinancing.")

    assert score.passed is False


@pytest.mark.asyncio
async def test_answer_relevance_passes_for_structured_case_output() -> None:
    test_case = load_test_case("PR-003")
    runner_output = await MockRunner().run(test_case)

    score = await AnswerRelevanceEvaluator(
        DeterministicEmbeddingProvider()
    ).evaluate(test_case, runner_output.agent_output)

    assert score.passed is True
    assert "coverage" in score.reasoning


def test_answer_relevance_uses_sentence_transformers_by_default() -> None:
    evaluator = AnswerRelevanceEvaluator()

    assert isinstance(evaluator.embedding_provider, SentenceTransformerEmbeddingProvider)
