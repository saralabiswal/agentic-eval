"""Parsers for JSON responses returned by judge LLMs."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class ClaimAssessment(BaseModel):
    """Judge assessment for one factual claim."""

    claim: str
    evidence: str | None = None
    rating: str


class ChunkAssessment(BaseModel):
    """Judge assessment for one retrieved context chunk."""

    document_id: str
    rating: str
    reasoning: str


class JudgeResponse(BaseModel):
    """Typed, clamped judge response used by evaluators."""

    score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence: list[str] = Field(default_factory=list)
    claims: list[ClaimAssessment] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    chunk_assessments: list[ChunkAssessment] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("score", mode="before")
    @classmethod
    def clamp_score(cls, value: Any) -> float:
        """Clamp judge scores into the canonical 0.0 to 1.0 range."""

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(1.0, max(0.0, numeric))


def _strip_markdown_fences(content: str) -> str:
    fenced = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", content, re.DOTALL)
    if fenced:
        return fenced.group(1)
    return content.strip()


def parse_judge_response(content: str) -> JudgeResponse:
    """Parse a judge JSON string into a typed response without raising."""

    cleaned = _strip_markdown_fences(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return JudgeResponse(
            score=0.0,
            reasoning=f"Malformed judge JSON: {exc.msg}",
            evidence=[],
            raw={"content": content},
        )

    if not isinstance(payload, dict):
        return JudgeResponse(
            score=0.0,
            reasoning="Judge response JSON was not an object.",
            evidence=[],
            raw={"content": payload},
        )

    normalized = {
        "score": payload.get("score", 0.0),
        "reasoning": str(payload.get("reasoning", "Judge response missing reasoning.")),
        "evidence": payload.get("evidence", []),
        "claims": payload.get("claims", []),
        "unsupported_claims": payload.get("unsupported_claims", []),
        "chunk_assessments": payload.get("chunk_assessments", []),
        "raw": payload,
    }
    try:
        return JudgeResponse.model_validate(normalized)
    except ValidationError as exc:
        return JudgeResponse(
            score=0.0,
            reasoning=f"Judge response validation failed: {exc.errors()[0]['msg']}",
            evidence=[],
            raw=payload,
        )
