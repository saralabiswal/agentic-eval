"""Versioned LLM-as-judge prompt templates."""

FAITHFULNESS_PROMPT_V1 = """
You are evaluating whether an AI agent's output is faithful to
the provided context. Faithful means every factual claim in the
output can be traced to the context. Do not use external knowledge.

Context (retrieved policy chunks):
{context}

Agent Output:
{agent_output}

For each factual claim in the agent output:
1. State the claim
2. Find supporting evidence in the context (exact quote)
3. Rate: SUPPORTED | UNSUPPORTED | PARTIALLY_SUPPORTED

Then compute: score = supported_claims / total_claims

Return JSON only:
{{
  "claims": [
    {{"claim": str, "evidence": str, "rating": str}}
  ],
  "score": float,
  "reasoning": str,
  "unsupported_claims": [str]
}}
"""

ANSWER_RELEVANCE_PROMPT_V1 = """
You are evaluating whether an AI agent's output answers the scenario
it was asked to address. Relevant means the output responds directly
to the user question and uses the scenario context.

Question / Scenario:
{context}

Agent Output:
{agent_output}

Rate whether the output is relevant to the scenario on a 0.0 to 1.0
scale. Penalize outputs that are off-topic, omit the requested decision,
or discuss unrelated customer actions.

Return JSON only:
{{
  "score": float,
  "reasoning": str,
  "evidence": [str]
}}
"""

CONTEXT_PRECISION_PROMPT_V1 = """
You are evaluating retrieval quality for a RAG (retrieval-augmented
generation) system. Your task is to assess whether each retrieved
document chunk was actually necessary to answer the question.

Question / Scenario:
{context}

Agent Output:
{agent_output}

For each chunk, answer: Was this chunk NECESSARY to produce the output?
- NECESSARY: The output references or relies on information from this chunk
- HELPFUL: The chunk is related but not directly used
- NOISE: The chunk is unrelated to the output; retrieval error

Compute: precision = necessary_chunks / total_chunks

Return JSON only:
{{
  "chunk_assessments": [
    {{
      "document_id": str,
      "rating": "NECESSARY | HELPFUL | NOISE",
      "reasoning": str
    }}
  ],
  "score": float,
  "reasoning": str
}}
"""

FAITHFULNESS_PROMPT_CURRENT = FAITHFULNESS_PROMPT_V1
ANSWER_RELEVANCE_PROMPT_CURRENT = ANSWER_RELEVANCE_PROMPT_V1
CONTEXT_PRECISION_PROMPT_CURRENT = CONTEXT_PRECISION_PROMPT_V1
