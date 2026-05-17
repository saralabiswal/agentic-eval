.PHONY: install dev test lint typecheck format demo docker-up docker-down ollama-models ollama-smoke

install:
	uv sync --all-extras
	cd ui && corepack pnpm install

dev:
	uv run uvicorn eval.api.main:app --host 0.0.0.0 --port 8001 --reload

test:
	uv run pytest --no-cov || [ $$? -eq 5 ]

lint:
	uv run ruff check .

typecheck:
	uv run mypy eval

format:
	uv run ruff format .

demo:
	uv run python -m eval.demo

docker-up:
	docker compose up -d ollama

docker-down:
	docker compose down

ollama-models:
	ollama pull llama3.2
	ollama pull qwen2.5:7b

ollama-smoke:
	uv run python -m eval.ollama_smoke
