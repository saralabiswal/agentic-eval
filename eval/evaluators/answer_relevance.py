"""Answer relevance evaluator using semantic embeddings."""

from __future__ import annotations

import asyncio
import re

from eval.core.schemas import DimensionScore, TestCase
from eval.evaluators._utils import case_arg_parser, load_test_case
from eval.evaluators.embeddings import (
    EmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    cosine_similarity,
)

_STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "has",
    "into",
    "only",
    "rather",
    "than",
    "that",
    "the",
    "this",
    "with",
}


class AnswerRelevanceEvaluator:
    """Score semantic relevance and task coverage between scenario and output."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or SentenceTransformerEmbeddingProvider()

    async def evaluate(
        self,
        test_case: TestCase,
        agent_output: str,
    ) -> DimensionScore:
        """Evaluate answer relevance for a test case output."""

        question_vector, answer_vector = await self.embedding_provider.embed(
            [test_case.input.scenario_context, agent_output]
        )
        semantic_score = cosine_similarity(question_vector, answer_vector)
        coverage_score, coverage_evidence = self._task_coverage_score(test_case, agent_output)
        score = round(max(semantic_score, coverage_score), 4)
        return DimensionScore(
            score=score,
            passed=score >= test_case.evaluation_criteria.answer_relevance_threshold,
            threshold=test_case.evaluation_criteria.answer_relevance_threshold,
            reasoning=(
                "Semantic similarity calibrated with task coverage "
                f"(embedding={semantic_score:.4f}, coverage={coverage_score:.4f})."
            ),
            evidence=[test_case.input.scenario_context, *coverage_evidence],
        )

    def _task_coverage_score(
        self,
        test_case: TestCase,
        agent_output: str,
    ) -> tuple[float, list[str]]:
        """Estimate whether the answer covers the requested decision surface."""

        output_tokens = _tokens(agent_output)
        output_text = _normalized_text(agent_output)
        scenario_tokens = _tokens(test_case.input.scenario_context)
        scenario_score = _token_coverage(scenario_tokens, output_tokens)

        policy_score = _policy_citation_score(test_case, output_text)
        components: list[tuple[float, float, str]] = [
            (0.15, scenario_score, "scenario terms"),
            (0.20, policy_score, "policy citation"),
        ]
        evidence: list[str] = []
        if scenario_score >= 0.50:
            evidence.append("scenario terms covered")
        if policy_score:
            evidence.append("policy context referenced")

        action = test_case.expected.expected_action_type
        if action:
            action_score = (
                1.0
                if _phrase_or_tokens_present(action, output_text, output_tokens)
                else 0.0
            )
            components.append((0.25, action_score, f"action {action}"))
            if action_score:
                evidence.append(f"action: {action}")

        risk_level = test_case.expected.risk_level
        if risk_level:
            risk_score = 1.0 if risk_level.lower() in output_tokens else 0.0
            components.append((0.20, risk_score, f"risk {risk_level}"))
            if risk_score:
                evidence.append(f"risk: {risk_level}")

        key_signal_score = _key_signal_coverage(
            test_case.expected.key_signals,
            output_text,
            output_tokens,
        )
        if test_case.expected.key_signals:
            components.append((0.20, key_signal_score, "key signals"))
            if key_signal_score:
                evidence.append(f"key signal coverage: {key_signal_score:.2f}")

        total_weight = sum(weight for weight, _, _ in components)
        if total_weight == 0:
            return 0.0, evidence
        score = sum(weight * value for weight, value, _ in components) / total_weight
        return round(score, 4), evidence


def _normalized_text(text: str) -> str:
    return " ".join(_tokens(text))


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
        if len(token) > 2 and token not in _STOPWORDS
    }


def _token_coverage(expected_tokens: set[str], output_tokens: set[str]) -> float:
    if not expected_tokens:
        return 0.0
    return len(expected_tokens & output_tokens) / len(expected_tokens)


def _phrase_or_tokens_present(
    phrase: str,
    output_text: str,
    output_tokens: set[str],
) -> bool:
    expected_text = _normalized_text(phrase)
    expected_tokens = _tokens(phrase)
    return bool(expected_text and expected_text in output_text) or expected_tokens <= output_tokens


def _key_signal_coverage(
    key_signals: list[str],
    output_text: str,
    output_tokens: set[str],
) -> float:
    if not key_signals:
        return 0.0
    matched = sum(
        1
        for signal in key_signals
        if _key_signal_present(signal, output_text, output_tokens)
    )
    return matched / len(key_signals)


def _key_signal_present(
    signal: str,
    output_text: str,
    output_tokens: set[str],
) -> bool:
    signal_tokens = _tokens(signal)
    if not signal_tokens:
        return False
    if _phrase_or_tokens_present(signal, output_text, output_tokens):
        return True
    return _token_coverage(signal_tokens, output_tokens) >= 0.50


def _policy_citation_score(test_case: TestCase, output_text: str) -> float:
    output_tokens = set(output_text.split())
    document_token_sets = [
        _tokens(str(chunk.get("document_id", "")))
        for chunk in test_case.input.retrieved_policy_chunks
        if chunk.get("document_id")
    ]
    if not document_token_sets:
        return 0.0
    if any(document_tokens <= output_tokens for document_tokens in document_token_sets):
        return 1.0
    return 0.0


async def _main() -> None:
    parser = case_arg_parser("Run the answer relevance evaluator.")
    args = parser.parse_args()
    test_case = load_test_case(str(args.case))
    output = test_case.input.scenario_context
    await AnswerRelevanceEvaluator().evaluate(test_case, output)


if __name__ == "__main__":
    asyncio.run(_main())
