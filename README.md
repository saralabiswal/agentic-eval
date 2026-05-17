# agentic-eval

Evaluation framework for LLM-powered agentic systems across faithfulness,
answer relevance, context precision, response consistency, and latency/quality
tradeoff.

The framework is mock-first: a clean checkout can run a complete benchmark
without API keys, cloud calls, or the banking platform running.

## Quick Start — No API Key Required

```bash
git clone https://github.com/saralabiswal/agentic-eval
cd agentic-eval
make install
cp .env.example .env
make demo

# Evaluates 3 test cases with mock judge + mock SUT
# No API key. Deterministic results. Runs in seconds.
```

## With a real judge LLM (recommended):

```bash
echo "EVAL_JUDGE_BACKEND=api" >> .env
echo "EVAL_JUDGE_MODEL=gpt-4o" >> .env
echo "OPENAI_API_KEY=your-key" >> .env
make demo
```

## No API Key: Two Local Ollama Models

For a fully local setup, use Ollama for both the judge and the system under
test, but choose different models to reduce self-evaluation bias.

```bash
make docker-up
ollama pull llama3.2
ollama pull qwen2.5:7b
```

Then configure `.env`:

```env
EVAL_JUDGE_BACKEND=ollama
EVAL_JUDGE_MODEL=qwen2.5:7b

SUT_BACKEND=ollama
SUT_MODEL=llama3.2
```

This pairing keeps everything local and keyless: `llama3.2` is the model being
evaluated, while `qwen2.5:7b` acts as a separate judge. Using the exact same
model for both roles is allowed for experiments, but it is not recommended for
serious evaluation because it increases self-evaluation bias.

If your machine has more memory, `mistral-nemo:12b` is a stronger local judge
candidate:

```bash
ollama pull mistral-nemo:12b
```

## Architecture

```text
YAML test cases
  -> Runner (mock, direct, Ollama, API, platform)
  -> Evaluators (faithfulness, relevance, precision, consistency)
  -> BenchmarkReport
  -> Terminal, HTML, JSON, FastAPI/SSE
  -> React dashboard
```

The judge LLM is separate from the system under test. In development both can
be mock implementations so CI remains deterministic; in production the SUT can
be Ollama or an API model while the judge uses a separate stronger model.

## Evaluation Dimensions

**Faithfulness** checks whether every factual claim in the agent output is
grounded in retrieved policy and customer context. Unsupported claims are
recorded as hallucinations.

**Answer relevance** checks whether the output addresses the scenario that was
asked, rather than returning adjacent but unhelpful account history.

**Context precision** measures retrieval quality: each retrieved chunk is rated
as necessary, helpful, or noise so teams can see when retrieval is wasting
tokens or confusing the agent.

**Consistency** runs the same case multiple times and scores output similarity.
In regulated workflows, identical inputs should produce stable assessments.

**Latency / quality tradeoff** compares backends by quality per second so teams
can choose a model that fits both accuracy expectations and latency budgets.

## Model Comparison Example

```text
Backend | Avg Score | Avg Latency | Quality / Second
mock    | 0.87      | 1ms         | 870.0
ollama  | 0.84      | 3200ms      | 0.26
api     | 0.93      | 6400ms      | 0.15
```

For a strict latency SLO, mock or local models are useful for development
feedback. For final quality review, use a separate cloud judge and compare SUT
backends with the dashboard.

## Why This Matters

Schema validation can prove that an action payload is shaped correctly, but it
cannot prove that the reasoning is faithful, relevant, stable, or efficient.
This project adds that missing evaluation layer for governed agentic systems.

## Development

```bash
make install
make test
make typecheck
make lint
cd ui && corepack pnpm dev
```

Run the API locally:

```bash
make dev
```

Open the dashboard at `http://localhost:5173`.

## Clean-Clone Verification

Use this checklist before handing off a branch or release:

```bash
make install
make test
make typecheck
make lint
make demo
cd ui && corepack pnpm typecheck
```

Generated benchmark outputs stay under `reports/` and are ignored by git.
Only curated screenshots or sample artifacts should be promoted into
`docs/assets/`.

## Contribution Guide

Add new evaluation scenarios as YAML under `test_cases/`. Keep test cases as
data only; evaluator behavior belongs in Python modules with tests. Every new
public class or method should include a docstring, and every new module should
have focused test coverage. Use `uv` for Python and `pnpm` for the UI. Never
commit API keys, generated reports, cache directories, or private `.env` files.
