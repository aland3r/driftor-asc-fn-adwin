"""Tratamento da série antes do ADWIN, como nos scripts da pesquisa IPDD/ADWIN.

Modo ``raw``: a série entra no ADWIN como veio do log (reproduz a Tabela 1 do
artigo nas bases sintéticas). Modo ``treated``: picos isolados são trocados pela
média da vizinhança e a série é suavizada por média móvel centrada de
``min(15, max(3, n // 20))``. Mudanças de nível sustentadas são preservadas.

Funções puras, sem dependências externas.
"""

from __future__ import annotations

import statistics

def _is_isolated_spike(value: float, neighbours: list[float]) -> bool:
    """Return whether ``value`` is an isolated local spike."""
    if len(neighbours) < 2:
        return False

    centre = statistics.median(neighbours)
    deviations = [abs(item - centre) for item in neighbours]
    mad = statistics.median(deviations)
    distance = abs(value - centre)
    scale = max(abs(centre) * 0.05, 1e-9)

    if mad <= scale:
        return distance > max(scale * 6, 1e-9)

    robust_sigma = 1.4826 * mad
    return distance > 3.5 * robust_sigma


def replace_isolated_outliers(
    values: list[float],
    neighbour_window: int = 2,
) -> tuple[list[float], list[int]]:
    """Treat isolated spikes while preserving sustained level changes."""
    original = [float(value) for value in values]
    treated = original.copy()
    outliers: list[int] = []

    for index, value in enumerate(original):
        neighbours = [
            original[position]
            for position in range(
                max(0, index - neighbour_window),
                min(len(original), index + neighbour_window + 1),
            )
            if position != index
        ]
        if _is_isolated_spike(value, neighbours):
            treated[index] = sum(neighbours) / len(neighbours)
            outliers.append(index)

    return treated, outliers


def smoothing_window(observation_count: int) -> int:
    """Regra de janela dos scripts da pesquisa para a base real."""
    return min(15, max(3, observation_count // 20))


def centered_moving_average(values: list[float], window: int) -> list[float]:
    """Equivalent to pandas' centered rolling mean with ``min_periods=1``."""
    left = (window - 1) // 2
    right = window // 2
    averages: list[float] = []

    for index in range(len(values)):
        sample = values[
            max(0, index - left) : min(len(values), index + right + 1)
        ]
        averages.append(sum(sample) / len(sample))

    return averages


def estimate_change_start(
    values: list[float],
    detection_index: int,
    adaptive_width: int,
    segment_start: int = 0,
) -> int:
    """Locate the strongest two-regime split preceding an ADWIN detection."""
    lookback = max(adaptive_width * 4, 64)
    start = max(segment_start, detection_index - lookback + 1)
    sample = values[start : detection_index + 1]
    minimum_side = min(5, max(2, len(sample) // 4))
    if len(sample) < minimum_side * 2:
        return max(segment_start, detection_index - adaptive_width + 1)

    prefix = [0.0]
    prefix_squares = [0.0]
    for value in sample:
        prefix.append(prefix[-1] + value)
        prefix_squares.append(prefix_squares[-1] + value * value)

    def squared_error(left: int, right: int) -> float:
        count = right - left
        total = prefix[right] - prefix[left]
        squares = prefix_squares[right] - prefix_squares[left]
        return max(0.0, squares - total * total / count)

    candidates = range(minimum_side, len(sample) - minimum_side + 1)
    split = min(
        candidates,
        key=lambda position: squared_error(0, position)
        + squared_error(position, len(sample)),
    )
    return start + split
