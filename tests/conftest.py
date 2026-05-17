"""Shared pytest configuration for agentic-eval tests."""

from collections.abc import Iterator

import pytest

from eval.core.runtime_config import runtime_config


@pytest.fixture(autouse=True)
def reset_runtime_config() -> Iterator[None]:
    """Keep in-memory runtime config isolated between tests."""

    runtime_config.reset()
    yield
    runtime_config.reset()
