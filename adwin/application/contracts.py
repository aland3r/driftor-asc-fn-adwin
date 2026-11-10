"""Formato JSON das mensagens e da resposta HTTP (camelCase)."""

from __future__ import annotations

from adwin.domain.model import Detection, DetectionRequest


def request_from_json(body: dict) -> DetectionRequest:
    values = body.get("values")
    if not isinstance(values, list):
        from adwin.domain.model import InvalidSeries

        raise InvalidSeries("Envie 'values' como lista de números.")
    return DetectionRequest(
        values=values,
        delta=float(body.get("delta", 0.002)),
        treatment=str(body.get("treatment", "raw")),
    )


def detection_to_json(detection: Detection) -> dict:
    return {
        "treatment": detection.treatment,
        "delta": detection.delta,
        "observationCount": detection.observation_count,
        "smoothingWindow": detection.smoothing_window,
        "processedValues": detection.processed_values,
        "outlierIndices": detection.outlier_indices,
        "drifts": [
            {
                "index": d.index,
                "anomalyStartIndex": d.anomaly_start_index,
                "value": d.value,
                "width": d.width,
                "estimation": d.estimation,
                "meanBefore": d.mean_before,
                "meanAfter": d.mean_after,
                "changePercent": d.change_percent,
            }
            for d in detection.drifts
        ],
    }


def completed_message(analysis_id: str, detection: Detection) -> dict:
    return {"type": "analysis-completed", "analysisId": analysis_id, "status": "concluida", **detection_to_json(detection)}


def failed_message(analysis_id: str, error: str) -> dict:
    return {"type": "analysis-completed", "analysisId": analysis_id, "status": "falhou", "error": error}
