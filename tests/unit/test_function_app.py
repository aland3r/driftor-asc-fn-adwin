import json

import azure.functions as func

import function_app

SERIES = [10.0] * 60 + [40.0] * 60


def http(body):
    return func.HttpRequest(method="POST", url="/api/adwin", body=json.dumps(body).encode())


def test_http_returns_treated_series_and_drifts():
    response = function_app.adwin_http(http({"values": SERIES, "treatment": "treated"}))
    assert response.status_code == 200
    data = json.loads(response.get_body())
    assert len(data["processedValues"]) == 120 and data["drifts"]


def test_http_rejects_bad_input():
    assert function_app.adwin_http(http({"values": [1]})).status_code == 422
    bad = func.HttpRequest(method="POST", url="/api/adwin", body=b"{")
    assert function_app.adwin_http(bad).status_code == 400


class Out:
    def set(self, value):
        self.value = value


def queue_message(body):
    return func.ServiceBusMessage(body=json.dumps(body).encode())


def test_queue_publishes_completed_or_failed():
    out = Out()
    function_app.adwin_queue(queue_message({"analysisId": "a1", "values": SERIES, "delta": 0.002}), out)
    done = json.loads(out.value)
    assert done["analysisId"] == "a1" and done["status"] == "concluida" and done["drifts"]

    function_app.adwin_queue(queue_message({"analysisId": "a2", "values": [1]}), out)
    assert json.loads(out.value)["status"] == "falhou"
