from __future__ import annotations

import math
from dataclasses import dataclass, field

TREATMENT_RAW = "raw"
TREATMENT_TREATED = "treated"
TREATMENTS = (TREATMENT_RAW, TREATMENT_TREATED)


class InvalidSeries(ValueError):
    """Série que não pode ser analisada (vira 422 no HTTP e 'falhou' na fila)."""


@dataclass(frozen=True)
class DetectionRequest:
    values: list[float]
    delta: float = 0.002
    treatment: str = TREATMENT_RAW

    def validate(self) -> None:
        if len(self.values) < 2:
            raise InvalidSeries("A análise exige ao menos duas observações.")
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in self.values):
            raise InvalidSeries("A série contém valores numéricos inválidos.")
        if not 0 < self.delta < 1:
            raise InvalidSeries("δ precisa estar entre 0 e 1.")
        if self.treatment not in TREATMENTS:
            raise InvalidSeries(f"Tratamento desconhecido: {self.treatment}. Use 'raw' ou 'treated'.")


@dataclass(frozen=True)
class Drift:
    index: int
    anomaly_start_index: int
    value: float
    width: float
    estimation: float
    mean_before: float
    mean_after: float
    change_percent: float


@dataclass(frozen=True)
class Detection:
    treatment: str
    delta: float
    observation_count: int
    smoothing_window: int
    processed_values: list[float]
    outlier_indices: list[int]
    drifts: list[Drift] = field(default_factory=list)
