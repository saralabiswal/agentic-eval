"""Consistency evaluator for repeated system-under-test runs."""

from __future__ import annotations

import asyncio
from itertools import combinations

from eval.core.schemas import DimensionScore, TestCase
from eval.evaluators._utils import case_arg_parser, load_test_case
from eval.evaluators.embeddings import (
    EmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    cosine_similarity,
)
from eval.runners.base_runner import BaseRunner, RunnerOutput


class ConsistencyEvaluator:
    """Score output stability across repeated runs of the same test case."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or SentenceTransformerEmbeddingProvider()

    async def evaluate(
        self,
        test_case: TestCase,
        runner: BaseRunner,
        n_runs: int = 5,
    ) -> DimensionScore:
        """Run the same test case repeatedly and score pairwise similarity."""

        outputs: list[str] = []
        for _ in range(n_runs):
            result = await runner.run(test_case)
            outputs.append(result.agent_output)

        vectors = await self.embedding_provider.embed(outputs)
        matrix = self._similarity_matrix(vectors)
        pair_scores = [
            matrix[left][right]
            for left, right in combinations(range(len(outputs)), 2)
        ]
        score = round(sum(pair_scores) / len(pair_scores), 4) if pair_scores else 1.0
        stable_pairs = sum(1 for pair_score in pair_scores if pair_score >= 0.90)
        return DimensionScore(
            score=score,
            passed=score >= test_case.evaluation_criteria.consistency_threshold,
            threshold=test_case.evaluation_criteria.consistency_threshold,
            reasoning=f"{stable_pairs} of {len(pair_scores)} run pairs had similarity above 0.90.",
            run_outputs=outputs,
            similarity_matrix=matrix,
        )

    def _similarity_matrix(self, vectors: list[list[float]]) -> list[list[float]]:
        matrix: list[list[float]] = []
        for left in vectors:
            row: list[float] = []
            for right in vectors:
                row.append(cosine_similarity(left, right))
            matrix.append(row)
        return matrix


class _StaticRunner:
    def __init__(self, output: str) -> None:
        self.output = output

    async def run(self, test_case: TestCase) -> RunnerOutput:
        return RunnerOutput(
            agent_output=self.output,
            latency_ms=1,
            model_name="static",
            raw_response={"case_id": test_case.case_id},
        )


async def _main() -> None:
    parser = case_arg_parser("Run the consistency evaluator.")
    args = parser.parse_args()
    test_case = load_test_case(str(args.case))
    await ConsistencyEvaluator().evaluate(
        test_case,
        _StaticRunner(test_case.input.scenario_context),
    )


if __name__ == "__main__":
    asyncio.run(_main())
