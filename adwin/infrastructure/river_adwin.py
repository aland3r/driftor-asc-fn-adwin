"""Adapter do ADWIN da biblioteca river para a porta DriftDetector."""

from __future__ import annotations

from river.drift import ADWIN


def river_adwin(delta: float) -> ADWIN:
    return ADWIN(delta=delta)
