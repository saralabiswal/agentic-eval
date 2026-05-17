"""Integration tests for benchmark orchestration and API routes."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from eval.api.main import app
from eval.api.report_store import ReportStore, report_summary_row
from eval.benchmark import BenchmarkEngine, collect_events
from eval.core.runtime_config import RuntimeConfigUpdate, runtime_config


async def test_benchmark_engine_runs_all_cases_and_emits_events(tmp_path: Path) -> None:
    events, sink = await collect_events()
    report = await BenchmarkEngine(reports_dir=tmp_path, event_sink=sink).run(backend="mock")

    assert report.total_cases == 11
    assert len([event for event in events if event["event"] == "case_completed"]) == 11
    assert list(tmp_path.glob("*.html"))
    assert list(tmp_path.glob("*.json"))


def test_api_post_benchmark_run_returns_run_id() -> None:
    client = TestClient(app)

    response = client.post("/benchmark/run", json={"backend": "mock", "cases": ["PR-001"]})

    assert response.status_code == 200
    assert response.json()["run_id"].startswith("run_")


def test_api_invalid_backend_returns_clear_error() -> None:
    client = TestClient(app)

    response = client.post("/benchmark/run", json={"backend": "invalid"})

    assert response.status_code == 400
    assert "Unsupported backend" in response.json()["detail"]


def test_config_api_returns_no_secret_values() -> None:
    client = TestClient(app)

    response = client.get("/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["eval_judge_backend"] == "mock"
    assert "has_anthropic_api_key" not in payload
    assert payload["openai_model_options"]
    assert payload["ollama_judge_model_options"]
    assert payload["ollama_sut_model_options"]
    assert "ANTHROPIC_API_KEY" not in str(payload)
    assert "OPENAI_API_KEY" not in str(payload)


def test_config_connection_test_never_echoes_api_key() -> None:
    client = TestClient(app)

    response = client.post(
        "/config/test-connection",
        json={"target": "judge", "backend": "api", "api_key": "SECRET_TEST_KEY"},
    )

    assert response.status_code == 200
    assert "SECRET_TEST_KEY" not in str(response.json())
    assert response.json()["backend"] == "api"


def test_config_runtime_update_changes_effective_settings() -> None:
    client = TestClient(app)

    response = client.post(
        "/config/runtime",
        json={
            "eval_judge_backend": "ollama",
            "eval_judge_model": "qwen2.5:7b",
            "sut_backend": "ollama",
            "sut_model": "llama3.2",
        },
    )
    try:
        assert response.status_code == 200
        payload = response.json()
        assert payload["eval_judge_backend"] == "ollama"
        assert payload["eval_judge_model"] == "qwen2.5:7b"
        assert payload["sut_backend"] == "ollama"
        assert payload["sut_model"] == "llama3.2"
        assert client.get("/config").json()["sut_backend"] == "ollama"
    finally:
        runtime_config.reset()


def test_config_runtime_update_rejects_invalid_api_model() -> None:
    client = TestClient(app)

    response = client.post(
        "/config/runtime",
        json={"eval_judge_backend": "api", "eval_judge_model": "llama3.2"},
    )

    assert response.status_code == 400
    assert "API judge model" in response.json()["detail"]


def test_config_runtime_update_rejects_invalid_ollama_sut_model() -> None:
    client = TestClient(app)

    response = client.post(
        "/config/runtime",
        json={"sut_backend": "ollama", "sut_model": "mock-sut"},
    )

    assert response.status_code == 400
    assert "Ollama SUT model" in response.json()["detail"]


async def test_benchmark_engine_preserves_backend_labels(tmp_path: Path) -> None:
    report = await BenchmarkEngine(reports_dir=tmp_path).run(cases=["PR-001"], backend="ollama")

    assert report.model_backend == "ollama"
    assert report.results[0].model_backend == "ollama"


async def test_direct_non_mock_backend_uses_evaluable_output_shape(tmp_path: Path) -> None:
    report = await BenchmarkEngine(reports_dir=tmp_path).run(cases=["PR-003"], backend="ollama")
    result = report.results[0]

    assert result.model_backend == "ollama"
    assert result.agent_output
    assert 0.0 <= result.overall_score <= 1.0
    assert result.answer_relevance.passed is True
    assert result.context_precision.passed is True
    assert len(result.consistency.run_outputs) == 5
    assert len(result.consistency.similarity_matrix) == 5


async def test_benchmark_engine_uses_runtime_sut_backend_by_default(tmp_path: Path) -> None:
    runtime_config.update(RuntimeConfigUpdate(sut_backend="ollama", sut_model="llama3.2"))
    try:
        report = await BenchmarkEngine(reports_dir=tmp_path).run(cases=["PR-003"])
    finally:
        runtime_config.reset()

    assert report.model_backend == "ollama"
    assert report.results[0].model_backend == "ollama"


def test_make_demo_style_full_run_completes_quickly(tmp_path: Path) -> None:
    start = time.perf_counter()

    import asyncio

    report = asyncio.run(BenchmarkEngine(reports_dir=tmp_path).run(backend="mock"))

    assert report.total_cases == 11
    assert report.passed == 10
    assert report.failed == 1
    assert time.perf_counter() - start < 15


async def test_report_store_discovers_generated_reports_after_memory_clear(tmp_path: Path) -> None:
    report = await BenchmarkEngine(reports_dir=tmp_path).run(cases=["PR-001"], backend="mock")
    store = ReportStore(reports_dir=tmp_path)

    loaded = store.get_report(report.run_id, {})
    rows = [report_summary_row(item) for item in store.list_reports({})]

    assert loaded is not None
    assert loaded.run_id == report.run_id
    assert rows[0]["avg_faithfulness"] == report.summary.avg_faithfulness
    assert rows[0]["avg_latency_ms"] == report.summary.avg_latency_ms
