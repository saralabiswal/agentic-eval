"""Tests for judge prompt templates, parser, and mock judge."""

from __future__ import annotations

import pytest

from eval.judge.client import MockJudgeClient
from eval.judge.parsers import parse_judge_response
from eval.judge.prompts import (
    ANSWER_RELEVANCE_PROMPT_CURRENT,
    CONTEXT_PRECISION_PROMPT_CURRENT,
    FAITHFULNESS_PROMPT_CURRENT,
)


@pytest.mark.parametrize(
    "prompt",
    [
        FAITHFULNESS_PROMPT_CURRENT,
        ANSWER_RELEVANCE_PROMPT_CURRENT,
        CONTEXT_PRECISION_PROMPT_CURRENT,
    ],
)
def test_prompt_templates_contain_required_variables(prompt: str) -> None:
    assert "{context}" in prompt
    assert "{agent_output}" in prompt


@pytest.mark.asyncio
async def test_mock_judge_returns_valid_deterministic_response() -> None:
    judge = MockJudgeClient()
    context = "document_id: KB-PAY-007\ncontent: Card utilization above 70%."
    output = "Risk is critical due to card utilization."

    first = await judge.evaluate(FAITHFULNESS_PROMPT_CURRENT, context, output)
    second = await judge.evaluate(FAITHFULNESS_PROMPT_CURRENT, context, output)

    assert first == second
    assert 0.85 <= first.score <= 0.95
    assert first.reasoning


def test_parser_handles_markdown_fenced_json() -> None:
    parsed = parse_judge_response(
        '```json\n{"score": 0.9, "reasoning": "ok", "evidence": ["quote"]}\n```'
    )

    assert parsed.score == 0.9
    assert parsed.evidence == ["quote"]


def test_parser_handles_malformed_json_gracefully() -> None:
    parsed = parse_judge_response("{not valid json")

    assert parsed.score == 0.0
    assert "Malformed judge JSON" in parsed.reasoning


def test_parser_fails_closed_on_validation_errors() -> None:
    parsed = parse_judge_response(
        '{"score": 1.0, "reasoning": "ok", "unsupported_claims": [{"claim": "bad"}]}'
    )

    assert parsed.score == 0.0
    assert "Judge response validation failed" in parsed.reasoning


def test_parser_clamps_scores_outside_range() -> None:
    high = parse_judge_response('{"score": 1.8, "reasoning": "high"}')
    low = parse_judge_response('{"score": -0.2, "reasoning": "low"}')

    assert high.score == 1.0
    assert low.score == 0.0
