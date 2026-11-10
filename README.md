# Driftor ASC · fn-adwin

Azure Function do **Driftor ASC**, entrega 3 de Arquitetura e Soluções Cloud (PUCPR). Roda a detecção de desvios de desempenho IPDD/ADWIN sobre uma série de durações. É sem estado: recebe a série, devolve os desvios e não grava nada.

## Na nuvem

| | URL |
|---|---|
| HTTP | `POST https://driftor-asc-fn-adwin.azurewebsites.net/api/adwin` |
| Saúde | https://driftor-asc-fn-adwin.azurewebsites.net/api/health |
| Fila de entrada | `analysis-requested` (Service Bus `driftor-asc-bus`) |
| Fila de saída | `analysis-completed` |

## Duas formas de chamar

**Message Trigger (`adwin_queue`).** O [driftor-asc-ipdd](https://github.com/aland3r/driftor-asc-ipdd) cria a análise e publica em `analysis-requested`:

```json
{ "analysisId": "…", "values": [41.2, 39.8, …], "delta": 0.002, "treatment": "raw" }
```

A Function responde em `analysis-completed` com `status` `concluida` (desvios, outliers, série tratada) ou `falhou` (com `error`). O ipdd consome e grava o resultado no Azure SQL.

**HTTP Trigger (`adwin_http`).** `POST /api/adwin` com o mesmo corpo, sem `analysisId`. O [BFF](https://github.com/aland3r/driftor-asc-bff) usa no `GET /aggregated-data` para trazer a série tratada que o gráfico da análise mostra.

Resposta (as duas formas):

```json
{
  "treatment": "raw", "delta": 0.002, "observationCount": 500, "smoothingWindow": 1,
  "processedValues": [ … ], "outlierIndices": [],
  "drifts": [
    { "index": 140, "anomalyStartIndex": 121, "value": 52.0, "width": 96.0, "estimation": 50.7,
      "meanBefore": 40.1, "meanAfter": 50.9, "changePercent": 26.93 }
  ]
}
```

- `raw`: a série entra no ADWIN como veio do log, como nos scripts da pesquisa para as bases sintéticas.
- `treated`: picos isolados são trocados pela média da vizinhança e a série passa por média móvel centrada antes do ADWIN.

## Arquitetura

```
function_app.py                 gatilhos (Service Bus e HTTP), modelo Python v2
adwin/
  domain/                       série, desvio, tratamento e segmentos; funções puras
  application/
    detect_drifts/handler.py    o caso de uso
    contracts.py                JSON de entrada e saída
    ports.py                    interface do detector
  infrastructure/river_adwin.py adapter do ADWIN da biblioteca river
```

O teste de arquitetura roda os contratos do [import-linter](.importlinter): domínio e aplicação não importam `river` nem `azure`, e as camadas só dependem para dentro.

Os testes unitários conferem que, com a série de `Machine_Operating` das bases `ST_20`, `DR_20`, `DR_MS_20` e `DR_MS_ST_20`, δ = 0,002 e modo `raw`, saem 0, 4, 7 e 9 desvios, como na Tabela 1 do artigo.

## Tecnologias

Python 3.12, Azure Functions (modelo v2, plano Flex Consumption), Azure Service Bus, river (ADWIN), pytest, import-linter, GitHub Actions.

## Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
cp local.settings.example.json local.settings.json   # preencha SERVICEBUS_CONNECTION
func start                                           # Azure Functions Core Tools v4
curl -X POST localhost:7071/api/adwin -d '{"values":[1,1,1,5,5,5],"treatment":"raw"}'
```

## Pipeline

A cada push na `main`, o GitHub Actions roda os testes e publica na Function App `driftor-asc-fn-adwin` (Brazil South) com o secret `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`. A configuração `SERVICEBUS_CONNECTION` fica nas variáveis de ambiente da Function App.

## Grupo

- Alander Menezes Arantes de Ávila
- Bernardo Creplive Vieira
- Emanuelle Skolut Jose
- Murilo Regnier Stange
