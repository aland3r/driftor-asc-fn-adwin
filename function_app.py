"""Azure Function do Driftor ASC: IPDD/ADWIN por fila (Service Bus) e por HTTP.

- ``adwin_queue``: consome ``analysis-requested`` (publicada pelo ipdd) e
  responde em ``analysis-completed``.
- ``adwin_http``: ``POST /api/adwin`` devolve a série tratada, outliers e
  desvios sem gravar nada; o BFF usa no ``/aggregated-data``.
"""

import json
import logging

import azure.functions as func

from adwin.application.contracts import completed_message, detection_to_json, failed_message, request_from_json
from adwin.application.detect_drifts.handler import DetectDriftsHandler
from adwin.domain.model import InvalidSeries
from adwin.infrastructure.river_adwin import river_adwin

app = func.FunctionApp()
handler = DetectDriftsHandler(river_adwin)
log = logging.getLogger("fn-adwin")


@app.function_name("adwin_queue")
@app.service_bus_queue_trigger(arg_name="msg", queue_name="analysis-requested", connection="SERVICEBUS_CONNECTION")
@app.service_bus_queue_output(arg_name="out", queue_name="analysis-completed", connection="SERVICEBUS_CONNECTION")
def adwin_queue(msg: func.ServiceBusMessage, out: func.Out[str]) -> None:
    body = json.loads(msg.get_body().decode("utf-8"))
    analysis_id = str(body.get("analysisId", ""))
    try:
        detection = handler.handle(request_from_json(body))
        out.set(json.dumps(completed_message(analysis_id, detection)))
        log.info("análise %s concluída: %d desvios", analysis_id, len(detection.drifts))
    except InvalidSeries as err:
        out.set(json.dumps(failed_message(analysis_id, str(err))))
        log.warning("análise %s falhou: %s", analysis_id, err)


@app.function_name("adwin_http")
@app.route(route="adwin", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def adwin_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return _json({"detail": "Corpo JSON inválido."}, 400)
    try:
        return _json(detection_to_json(handler.handle(request_from_json(body))), 200)
    except InvalidSeries as err:
        return _json({"detail": str(err)}, 422)


@app.function_name("health")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return _json({"status": "ok", "service": "fn-adwin"}, 200)


def _json(body: dict, status: int) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(body), status_code=status, mimetype="application/json")
