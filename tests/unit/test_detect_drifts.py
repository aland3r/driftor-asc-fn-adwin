import json
from pathlib import Path

import pytest

from adwin.application.detect_drifts.handler import DetectDriftsHandler
from adwin.domain.model import DetectionRequest, InvalidSeries
from adwin.infrastructure.river_adwin import river_adwin

FIXTURE = json.loads((Path(__file__).parents[1] / "fixtures" / "machine_operating_alfa.json").read_text())
handler = DetectDriftsHandler(river_adwin)


@pytest.mark.parametrize("name, expected", [("ST_20", 0), ("DR_20", 4), ("DR_MS_20", 7), ("DR_MS_ST_20", 9)])
def test_raw_mode_reproduces_the_article_table(name, expected):
    detection = handler.handle(DetectionRequest(values=FIXTURE[name], delta=0.002, treatment="raw"))
    assert len(detection.drifts) == expected
    assert detection.smoothing_window == 1 and detection.outlier_indices == []


def test_treated_mode_smooths_and_reports_outliers():
    values = [10.0] * 40 + [80.0] + [10.0] * 40 + [30.0] * 80
    detection = handler.handle(DetectionRequest(values=values, treatment="treated"))
    assert 40 in detection.outlier_indices
    assert detection.smoothing_window == 8
    assert detection.drifts, "a mudança sustentada de nível precisa aparecer"
    first = detection.drifts[0]
    assert first.mean_after > first.mean_before and first.change_percent > 0


@pytest.mark.parametrize("request_", [
    DetectionRequest(values=[1.0]),
    DetectionRequest(values=[1.0, float("nan")]),
    DetectionRequest(values=[1.0, 2.0], delta=2),
    DetectionRequest(values=[1.0, 2.0], treatment="x"),
])
def test_invalid_series(request_):
    with pytest.raises(InvalidSeries):
        handler.handle(request_)
