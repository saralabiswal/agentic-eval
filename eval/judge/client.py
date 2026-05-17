"""LLM-as-judge clients for mock, Ollama, and LiteLLM backends."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

import httpx
import structlog

from eval.core.config import settings
from eval.core.exceptions import JudgeError
from eval.core.runtime_config import Backend, runtime_config
from eval.judge.parsers import JudgeResponse, parse_judge_response
from eval.judge.prompts import CONTEXT_PRECISION_PROMPT_CURRENT

logger = structlog.get_logger(__name__)

_CONTEXT_STOPWORDS = {
    "above",
    "after",
    "before",
    "below",
    "should",
    "than",
    "that",
    "the",
    "this",
    "with",
}


class JudgeClient(Protocol):
    """Protocol implemented by all judge clients."""

    async def evaluate(
        self,
        prompt_template: str,
        context: str,
        agent_output: str,
    ) -> JudgeResponse:
        """Evaluate an agent output with a judge prompt template."""


class MockJudgeClient:
    """Deterministic mock judge that returns realistic development scores."""

    async def evaluate(
        self,
        prompt_template: str,
        context: str,
        agent_output: str,
    ) -> JudgeResponse:
        """Return a deterministic judge response without external calls."""

        if prompt_template == CONTEXT_PRECISION_PROMPT_CURRENT:
            return self._context_precision_response(context=context, agent_output=agent_output)
        return self._faithfulness_or_relevance_response(
            context=context,
            agent_output=agent_output,
        )

    def _faithfulness_or_relevance_response(
        self,
        context: str,
        agent_output: str,
    ) -> JudgeResponse:
        lowered_context = context.lower()
        lowered_output = agent_output.lower()
        unsupported = [
            token
            for token in (
                "premium_tier",
                "premium tier",
                "long_tenure",
                "long tenure",
                "loyalty_discount",
                "loyalty discount",
                "nps",
                "tenure_months",
            )
            if token in lowered_output and token not in lowered_context
        ]
        score = 0.91 if not unsupported else 0.78
        payload: dict[str, Any] = {
            "claims": [
                {
                    "claim": "Agent output is grounded in supplied context.",
                    "evidence": context[:180],
                    "rating": "SUPPORTED",
                }
            ],
            "score": score,
            "reasoning": (
                "Mock judge found context support for the output."
                if not unsupported
                else "Mock judge found unsupported hallucination guard claims."
            ),
            "unsupported_claims": unsupported,
            "evidence": [] if unsupported else [context[:180]],
        }
        return JudgeResponse.model_validate({**payload, "raw": payload})

    def _context_precision_response(
        self,
        context: str,
        agent_output: str,
    ) -> JudgeResponse:
        chunks = _extract_context_chunks(context)
        if not chunks:
            chunks = [{"document_id": "context", "content": context}]

        lowered_output = agent_output.lower()
        output_tokens = _context_tokens(agent_output)
        assessments: list[dict[str, str]] = []
        score_total = 0.0
        for chunk in chunks:
            document_id = chunk["document_id"]
            content = chunk["content"]
            content_tokens = _context_tokens(content)
            overlap = len(content_tokens & output_tokens)
            rating = "HELPFUL"
            if document_id.lower() in lowered_output or overlap >= 2:
                rating = "NECESSARY"
                score_total += 1.0
            elif (
                "contact frequency" in content.lower()
                or "kb-comp" in document_id.lower()
                or "wrong product" in content.lower()
            ):
                rating = "NOISE"
            else:
                score_total += 0.5
            assessments.append(
                {
                    "document_id": document_id,
                    "rating": rating,
                    "reasoning": f"Mock retrieval assessment marked {document_id} as {rating}.",
                }
            )

        score = score_total / len(chunks)
        payload = {
            "chunk_assessments": assessments,
            "score": score,
            "reasoning": "Mock judge assessed retrieved chunk usefulness.",
            "evidence": [assessment["document_id"] for assessment in assessments],
        }
        return JudgeResponse.model_validate({**payload, "raw": payload})


class OllamaJudgeClient:
    """Judge client that calls a local Ollama chat model."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 180.0,
    ) -> None:
        self.model = model or settings.EVAL_JUDGE_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout_seconds = timeout_seconds

    async def evaluate(
        self,
        prompt_template: str,
        context: str,
        agent_output: str,
    ) -> JudgeResponse:
        """Evaluate by sending the filled prompt to Ollama."""

        prompt = prompt_template.format(context=context, agent_output=agent_output)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
        if response.status_code >= 400:
            raise JudgeError(f"Ollama judge failed with status {response.status_code}")
        payload = response.json()
        return parse_judge_response(str(payload.get("response", "")))


class LiteLLMJudgeClient:
    """Judge client that calls a cloud model through LiteLLM."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.EVAL_JUDGE_MODEL

    async def evaluate(
        self,
        prompt_template: str,
        context: str,
        agent_output: str,
    ) -> JudgeResponse:
        """Evaluate by sending the filled prompt to LiteLLM."""

        try:
            from litellm import acompletion
        except ImportError as exc:  # pragma: no cover
            raise JudgeError("LiteLLM is not installed.") from exc

        prompt = prompt_template.format(context=context, agent_output=agent_output)
        logger.debug("calling_litellm_judge", model=self.model)
        response = await acompletion(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an evaluation judge for AI systems. "
                        "Return JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        if content is None:
            raise JudgeError("LiteLLM judge returned empty content.")
        return parse_judge_response(str(content))


def create_judge_client(
    backend: Backend | None = None,
    model: str | None = None,
) -> JudgeClient:
    """Create a judge client from explicit or runtime configuration."""

    effective = runtime_config.get()
    selected_backend = backend or effective.eval_judge_backend
    selected_model = model or effective.eval_judge_model
    if selected_backend == "mock":
        return MockJudgeClient()
    if selected_backend == "ollama":
        return OllamaJudgeClient(model=selected_model)
    return LiteLLMJudgeClient(model=selected_model)


def judge_response_to_json(response: JudgeResponse) -> str:
    """Serialize a judge response for debugging and tests."""

    return json.dumps(response.model_dump(), sort_keys=True)


def _extract_context_chunks(context: str) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    for segment in context.split("\n---\n"):
        document_id = ""
        content_lines: list[str] = []
        in_content = False
        for line in segment.splitlines():
            stripped = line.strip()
            if stripped.startswith("document_id:"):
                document_id = stripped.split(":", 1)[1].strip()
                in_content = False
            elif stripped.startswith("content:"):
                content_lines.append(stripped.split(":", 1)[1].strip())
                in_content = True
            elif stripped.startswith("version:"):
                in_content = False
            elif in_content:
                content_lines.append(stripped)
        if document_id or content_lines:
            chunks.append(
                {
                    "document_id": document_id or "context",
                    "content": " ".join(content_lines),
                }
            )
    return chunks


def _context_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
        if len(token) > 3 and token not in _CONTEXT_STOPWORDS
    }
