# agentic-eval

Enterprise evaluation framework for LLM-powered agentic systems.

`agentic-eval` benchmarks whether an agentic workflow is grounded, relevant,
stable, and operationally practical before it is trusted in governed business
processes. It is built for pipelines that follow the pattern:

```text
retrieve context -> reason with an LLM -> propose a typed action -> evaluate evidence
```

The project is mock-first, local-first, and production-minded. A clean checkout
can run deterministic benchmarks with no API keys, then graduate to local
Ollama or cloud-backed model evaluation when a team is ready.

Author: Sarala Biswal

## What It Evaluates

| Dimension | Purpose | Enterprise risk addressed |
| --- | --- | --- |
| Faithfulness | Verifies factual claims against retrieved context | Unsupported claims and hallucinations |
| Answer relevance | Confirms the response addresses the scenario | Plausible but off-task answers |
| Context precision | Measures whether retrieved chunks were useful | Noisy retrieval and wasted tokens |
| Consistency | Re-runs the same case and compares outputs | Unstable decisions for identical inputs |
| Latency / quality | Compares quality against response time | Model choices that miss SLO expectations |

## Core Capabilities

- YAML-backed benchmark cases for repeatable governed scenarios.
- Separate Judge LLM and System Under Test (SUT) configuration.
- Mock, Ollama, and API execution modes.
- FastAPI service for benchmark execution, runtime settings, results, test cases,
  and server-sent live progress events.
- React dashboard for running benchmarks, browsing cases, inspecting results,
  comparing models, and understanding the architecture.
- HTML and JSON report generation for human review and machine processing.
- Startup report cleanup that keeps the latest generated report set manageable.
- No secret values returned through configuration APIs.

## Run Modes

| Mode | Judge | SUT | Best for |
| --- | --- | --- | --- |
| Mock | Deterministic mock judge | Deterministic mock SUT | CI, UI checks, repeatable local development |
| Local Ollama | `qwen2.5:7b` | `llama3.2` | No-key local model evaluation |
| API | OpenAI via LiteLLM | OpenAI via LiteLLM | Higher-quality final evaluation |
| Hybrid | API judge | Ollama SUT | Strong external judge over local model outputs |

The Judge and SUT should remain separate. Asking the same model to grade itself
can hide quality issues and creates self-evaluation bias.

## Architecture

```text
YAML test cases
  -> BenchmarkEngine
  -> Runner
       - MockRunner
       - OllamaRunner
       - ApiRunner
       - PlatformRunner
  -> CompositeEvaluator
       - FaithfulnessEvaluator
       - AnswerRelevanceEvaluator
       - ContextPrecisionEvaluator
       - ConsistencyEvaluator
  -> BenchmarkReport
  -> JSON / HTML reports
  -> FastAPI results API + SSE events
  -> React dashboard
```

### Runtime Flow

1. A user selects a benchmark preset and test case group in the dashboard.
2. The UI saves runtime model settings through `POST /config/runtime`.
3. The UI starts a run through `POST /benchmark/run`.
4. FastAPI creates a run id and background task.
5. `BenchmarkEngine` loads matching YAML cases from `test_cases/`.
6. The selected runner calls the SUT and captures raw response metadata.
7. `CompositeEvaluator` scores the output across all evaluation dimensions.
8. Reporters persist JSON and HTML outputs under `reports/`.
9. The UI streams progress from `/benchmark/events/{run_id}` and reads results
   from `/results`.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- `uv`
- `corepack` with `pnpm`
- Docker and the Ollama CLI only if using local Ollama

### Deterministic Local Run

```bash
git clone https://github.com/saralabiswal/agentic-eval
cd agentic-eval
make install
cp .env.example .env
make demo
```

Default behavior uses mock judge + mock SUT. It requires no API key and is
designed for repeatable development and CI checks.

### Fully Local Ollama Run

```bash
make docker-up
make ollama-models
make ollama-smoke
```

Recommended local `.env` pairing:

```env
EVAL_JUDGE_BACKEND=ollama
EVAL_JUDGE_MODEL=qwen2.5:7b

SUT_BACKEND=ollama
SUT_MODEL=llama3.2
```

This keeps evaluation local and keyless while preserving Judge/SUT separation:
Qwen judges Llama outputs.

### API-Backed Run

```bash
cp .env.example .env
```

Set:

```env
EVAL_JUDGE_BACKEND=api
EVAL_JUDGE_MODEL=gpt-4o
SUT_BACKEND=api
SUT_MODEL=gpt-4o
OPENAI_API_KEY=your-key
```

Then run:

```bash
make demo
```

## Running the Application

Start the API:

```bash
make dev
```

Start the UI:

```bash
cd ui
corepack pnpm dev
```

Open:

```text
http://localhost:5173
```

The API listens on port `8001` so it can run beside the banking platform on
port `8000`.

## API Surface

| Endpoint | Purpose |
| --- | --- |
| `POST /benchmark/run` | Start a benchmark in the background |
| `GET /benchmark/{run_id}` | Read run status or completed report |
| `GET /benchmark/events/{run_id}` | Stream live benchmark events |
| `GET /results` | List completed benchmark reports |
| `GET /results/{run_id}` | Fetch a full report |
| `GET /cases` | List YAML-backed test cases |
| `GET /cases/{case_id}` | Fetch one test case |
| `GET /config` | Return non-secret effective runtime config |
| `POST /config/runtime` | Update non-secret runtime model selection |
| `POST /config/test-connection` | Check backend reachability without echoing secrets |

## Repository Layout

```text
eval/
  api/          FastAPI routers, state, report loading, startup cleanup
  core/         Pydantic schemas, settings, runtime config, exceptions
  evaluators/   Faithfulness, relevance, precision, consistency, latency
  judge/        Mock, Ollama, and LiteLLM judge clients
  reporters/    JSON, HTML, and terminal report generation
  runners/      Mock, Ollama, API, platform, and direct runners

test_cases/     YAML benchmark definitions
tests/          Unit and integration coverage
ui/             React + Vite dashboard
reports/        Generated reports; only .gitkeep is tracked
```

Planning materials are intentionally kept under `docs/planning/` and ignored by
git. Generated reports, build outputs, caches, and local virtual environments
are also ignored.

## Quality Gates

Run these before handing off a branch:

```bash
make test
make typecheck
make lint
cd ui && corepack pnpm typecheck
```

Optional release confidence checks:

```bash
make demo
make ollama-smoke
cd ui && corepack pnpm build
```

## Security and Governance Notes

- `.env` is ignored and must not be committed.
- API keys are never returned from `/config` or connection-test responses.
- Mock mode keeps tests deterministic and avoids accidental cloud calls.
- Ollama mode calls the configured local `OLLAMA_BASE_URL`.
- API mode requires an explicit key and should be used deliberately.
- Judge and SUT settings are independent to avoid self-evaluation by default.
- Every benchmark result records evidence, hallucination flags, raw response
  metadata, latency, and pass/fail status.

## Adding Test Cases

Add YAML files under `test_cases/<scenario>/`.

Each case should include:

- Customer profile input.
- Retrieved policy chunks.
- Scenario context.
- Expected risk/action signals.
- Hallucination guards.
- Per-dimension thresholds.

Keep test cases as data. Evaluator behavior belongs in Python modules with
focused unit or integration tests.

## Development Standards

- Use `uv` for Python dependency management.
- Use `pnpm` through `corepack` for the UI.
- Add type hints to Python function signatures.
- Use Pydantic models for cross-boundary schemas.
- Keep public classes and methods documented.
- Prefer async I/O for runtime evaluation paths.
- Never commit generated reports, cache directories, local planning files,
  virtual environments, or API keys.

## License

MIT, as declared in `pyproject.toml`.
