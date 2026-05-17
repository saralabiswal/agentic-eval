"""agentic-eval demo entry point using the configured SUT backend."""

from __future__ import annotations

import argparse
import asyncio

from eval.benchmark import BenchmarkEngine
from eval.reporters.terminal_reporter import TerminalReporter


async def run_demo(case_ids: list[str] | None = None, backend: str | None = None) -> None:
    """Run a small benchmark demo with the configured or requested backend."""

    report = await BenchmarkEngine().run(cases=case_ids, backend=backend)
    TerminalReporter().render(report)


def main() -> None:
    """Parse arguments and run the demo."""

    parser = argparse.ArgumentParser(description="Run the agentic-eval demo.")
    parser.add_argument("--cases", nargs="*", default=None)
    parser.add_argument("--all", action="store_true", help="Run all test cases")
    parser.add_argument("--backend", choices=["mock", "ollama", "api"], default=None)
    args = parser.parse_args()
    selected = None if args.all or args.cases is None else list(args.cases)
    asyncio.run(run_demo(selected, args.backend))


if __name__ == "__main__":
    main()
