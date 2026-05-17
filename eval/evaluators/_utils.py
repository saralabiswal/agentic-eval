"""Shared helpers for evaluator implementations."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import yaml

from eval.core.schemas import TestCase


def load_test_case(case_id: str, root: Path | None = None) -> TestCase:
    """Load a YAML test case by case identifier."""

    base = root or Path("test_cases")
    for path in base.glob("**/*.yaml"):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("case_id") == case_id:
            return TestCase.model_validate(payload)
    msg = f"Test case not found: {case_id}"
    raise ValueError(msg)


def context_from_chunks(chunks: list[dict[str, Any]]) -> str:
    """Render retrieved chunks for judge prompts."""

    rendered: list[str] = []
    for chunk in chunks:
        rendered.append(
            "\n".join(
                (
                    f"document_id: {chunk.get('document_id', '')}",
                    f"version: {chunk.get('version', '')}",
                    f"content: {chunk.get('content', '')}",
                )
            )
        )
    return "\n---\n".join(rendered)


def token_similarity(left: str, right: str) -> float:
    """Compute a deterministic lexical similarity in the 0.0 to 1.0 range."""

    left_tokens = set(_tokens(left))
    right_tokens = set(_tokens(right))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    cosine = overlap / math.sqrt(len(left_tokens) * len(right_tokens))
    jaccard = overlap / len(left_tokens | right_tokens)
    return round(max(0.0, min(1.0, (cosine * 0.7) + (jaccard * 0.3))), 4)


def _tokens(text: str) -> list[str]:
    return [
        token.strip(".,:;!?()[]{}\"'").lower()
        for token in text.split()
        if token.strip(".,:;!?()[]{}\"'")
    ]


def case_arg_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard standalone evaluator argument parser."""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--case", default="PR-001", help="Case ID to evaluate")
    return parser
