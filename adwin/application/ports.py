from __future__ import annotations

from typing import Protocol


class DriftDetector(Protocol):
    """Detector incremental (o ADWIN do river implementa esta forma)."""

    drift_detected: bool
    width: float
    estimation: float

    def update(self, value: float) -> None: ...


class DetectorFactory(Protocol):
    def __call__(self, delta: float) -> DriftDetector: ...
