"""Tests for the consistency evaluator."""

from __future__ import annotations

import pytest

from eval.core.schemas import TestCase as EvalTestCase
from eval.evaluators._utils import load_test_case
from eval.evaluators.consistency import ConsistencyEvaluator
from eval.evaluators.embeddings import (
    DeterministicEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from eval.runners.base_runner import RunnerOutput


class SequenceRunner:
    """Test runner that emits configured outputs in sequence."""

    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.index = 0

    async def run(self, test_case: EvalTestCase) -> RunnerOutput:
        output = self.outputs[self.index % len(self.outputs)]
        self.index += 1
        return RunnerOutput(
            agent_output=output,
            latency_ms=1,
            model_name="sequence",
            raw_response={"case_id": test_case.case_id},
        )


@pytest.mark.asyncio
async def test_consistency_scores_one_for_identical_outputs() -> None:
    test_case = load_test_case("CP-001")
    runner = SequenceRunner(["same output"] * 5)

    score = await ConsistencyEvaluator(
        DeterministicEmbeddingProvider()
    ).evaluate(test_case, runner, n_runs=5)

    assert score.score == 1.0
    assert score.passed is True


@pytest.mark.asyncio
async def test_consistency_scores_lower_for_different_outputs() -> None:
    test_case = load_test_case("CP-001")
    runner = SequenceRunner(["risk critical", "billing dispute", "digital engagement"])

    score = await ConsistencyEvaluator(
        DeterministicEmbeddingProvider()
    ).evaluate(test_case, runner, n_runs=3)

    assert 0.0 <= score.score < 1.0
    assert len(score.run_outputs) == 3
    assert isinstance(score.similarity_matrix, list)


def test_consistency_uses_sentence_transformers_by_default() -> None:
    evaluator = ConsistencyEvaluator()

    assert isinstance(evaluator.embedding_provider, SentenceTransformerEmbeddingProvider)
