"""Caso de uso único da Function: rodar o IPDD/ADWIN numa série."""

from __future__ import annotations

from adwin.application.ports import DetectorFactory
from adwin.domain.model import TREATMENT_RAW, Detection, DetectionRequest, Drift
from adwin.domain.segments import change_percent, segment_means
from adwin.domain.treatment import (
    centered_moving_average,
    estimate_change_start,
    replace_isolated_outliers,
    smoothing_window,
)


class DetectDriftsHandler:
    def __init__(self, detector_factory: DetectorFactory):
        self._new_detector = detector_factory

    def handle(self, request: DetectionRequest) -> Detection:
        request.validate()
        values = [float(v) for v in request.values]

        if request.treatment == TREATMENT_RAW:
            processed, outliers, window = values, [], 1
        else:
            treated, outliers = replace_isolated_outliers(values)
            window = smoothing_window(len(treated))
            processed = centered_moving_average(treated, window)

        detector = self._new_detector(request.delta)
        raw_drifts: list[tuple[int, int, float, float, float]] = []
        segment_start = 0
        for index, value in enumerate(processed):
            detector.update(value)
            if detector.drift_detected:
                start = estimate_change_start(processed, index, int(detector.width), segment_start)
                raw_drifts.append((index, start, value, float(detector.width), float(detector.estimation)))
                segment_start = index + 1

        means = segment_means(processed, [d[1] for d in raw_drifts])
        drifts = [
            Drift(
                index=index,
                anomaly_start_index=start,
                value=value,
                width=width,
                estimation=estimation,
                mean_before=round(before, 4),
                mean_after=round(after, 4),
                change_percent=change_percent(before, after),
            )
            for (index, start, value, width, estimation), (before, after) in zip(raw_drifts, means)
        ]
        return Detection(
            treatment=request.treatment,
            delta=request.delta,
            observation_count=len(values),
            smoothing_window=window,
            processed_values=processed,
            outlier_indices=outliers,
            drifts=drifts,
        )
