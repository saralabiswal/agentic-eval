"""Latency and quality tradeoff analyzer."""

from __future__ import annotations

import asyncio

from eval.core.schemas import BackendProfile, EvalResult, LatencyQualityReport


class LatencyQualityAnalyzer:
    """Compare quality per second across model backends."""

    async def analyze(
        self,
        results_by_backend: dict[str, EvalResult],
    ) -> LatencyQualityReport:
        """Compute efficiency profiles and a backend recommendation."""

        profiles: list[BackendProfile] = []
        for backend, result in results_by_backend.items():
            latency_seconds = max(result.latency_ms / 1000, 0.001)
            profiles.append(
                BackendProfile(
                    backend=backend,
                    overall_score=result.overall_score,
                    latency_ms=result.latency_ms,
                    efficiency_ratio=round(result.overall_score / latency_seconds, 4),
                )
            )
        profiles.sort(key=lambda profile: profile.efficiency_ratio, reverse=True)
        recommendation = (
            f"{profiles[0].backend} provides the best quality per second."
            if profiles
            else "No backend results were supplied."
        )
        return LatencyQualityReport(backends=profiles, recommendation=recommendation)


async def _main() -> None:
    await LatencyQualityAnalyzer().analyze({})


if __name__ == "__main__":
    asyncio.run(_main())
