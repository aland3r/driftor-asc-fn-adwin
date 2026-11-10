"""Médias antes/depois de cada desvio (segmentos entre desvios)."""

from __future__ import annotations


def segment_means(values: list[float], starts: list[int]) -> list[tuple[float, float]]:
    """Para cada início de anomalia, média do segmento anterior e do seguinte."""
    bounds = [0, *starts, len(values)]
    result: list[tuple[float, float]] = []
    for position, start in enumerate(starts, start=1):
        before = values[bounds[position - 1] : start] or values[:1]
        after = values[start : bounds[position + 1]] or values[-1:]
        result.append((sum(before) / len(before), sum(after) / len(after)))
    return result


def change_percent(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round((after - before) / abs(before) * 100, 2)
