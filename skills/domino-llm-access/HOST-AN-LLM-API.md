# Host an LLM: REST API reference

Applies to Domino 6.3 and Domino Cloud. Every route below is present in both public specs (6.3.1 and 6.4.0) under the `/api/gen-ai/beta` prefix. The prefix is `beta`; re-check `GET $DOMINO_API_HOST/assets/public-api.json` on the deployment before generating client code.

## Authentication

```python
import os, requests

if os.environ.get("DOMINO_API_PROXY"):                       # in-run, JWT credential propagation
    base_url, headers = os.environ["DOMINO_API_PROXY"].rstrip("/"), {}
else:                                                        # in-run, access-token sidecar
    base_url = os.environ["DOMINO_API_HOST"].rstrip("/")
    token = requests.get("http://localhost:8899/access-token").text.strip()
    headers = {"Authorization": f"Bearer {token}"}
# Outside a run: base_url = the deployment's HTTPS URL, headers = Bearer <Personal Access Token>
```

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/gen-ai/beta/default-endpoint-environment` | The default environment for endpoints (the Domino vLLM Environment) |
| GET | `/api/gen-ai/beta/endpoints?projectId=&registeredModelName=` | List endpoints, optionally filtered |
| POST | `/api/gen-ai/beta/endpoints` | Create an endpoint with its first version |
| GET | `/api/gen-ai/beta/endpoints/{endpointId}` | Endpoint detail, including `url` and `currentVersion.status` |
| DELETE | `/api/gen-ai/beta/endpoints/{endpointId}` | Delete the endpoint |
| GET | `/api/gen-ai/beta/endpoints/{endpointId}/collaborators` | Who has access |
| GET | `/api/gen-ai/beta/endpoints/{endpointId}/versions` | Versions of the endpoint |
| GET | `/api/gen-ai/beta/endpoints/{endpointId}/versions/{versionNumber}` | One version |
| PATCH | `/api/gen-ai/beta/endpoints/{endpointId}/versions/{versionNumber}` | Change a version (model source, environment, tier, configuration, access, vanity URL, instructions) |
| POST | `/api/gen-ai/beta/endpoints/{endpointId}/versions/{versionNumber}/start` | Start a version |
| POST | `/api/gen-ai/beta/endpoints/{endpointId}/versions/{versionNumber}/stop` | Stop a version |
| GET | `.../versions/{versionNumber}/request-metrics` | Request metrics |
| GET | `.../versions/{versionNumber}/vllm-token-metrics` | Token metrics from vLLM |
| GET | `.../versions/{versionNumber}/vllm-latency-metrics` | Latency metrics from vLLM |
| GET | `.../versions/{versionNumber}/pod-resource-metrics` | CPU, memory and GPU usage of the serving pod |
| GET | `.../versions/{versionNumber}/realTimeLogs?logType=&limit=&offset=&latestTime=` | Live logs of the serving execution |
| GET | `/api/gen-ai/beta/vanity-url-availability/{vanityUrl}` | Whether a vanity URL is free |

All four metrics routes take the same query parameters: `startTime`, `endTime`, `aggregationWindow`, `maxHistoricalExecutions`.

## Create an endpoint

Required fields: `name`, `projectId`, `modelSource`, `environment`, `hardwareTierId`, `configuration`, `generalAccess`, `collaborators`. Exactly one of the two `modelSource` shapes is used.

```python
env = requests.get(f"{base_url}/api/gen-ai/beta/default-endpoint-environment", headers=headers).json()

body = {
    "name": "llama-3-8b-chat",
    "description": "Chat model for the support assistant",
    "projectId": os.environ["DOMINO_PROJECT_ID"],
    "modelSource": {
        # From Hugging Face:
        "huggingFace": {
            "path": "meta-llama/Meta-Llama-3-8B-Instruct",   # repo path on Hugging Face
            "commit": "main",                                 # revision
            "apiToken": os.environ.get("HF_TOKEN", ""),       # needed for gated models
            "modelType": "LLM",                               # LLM | Embedding | OtherGenAI
        },
        # Or from the Domino Model Registry instead:
        # "registeredModel": {"modelName": "support-llm", "modelVersion": 3},
    },
    "environment": {"environmentId": env["id"]},              # add "revisionId" only to pin a specific revision; optional
    "hardwareTierId": "gpu-a10g-24gb",                        # a GPU tier id from the deployment
    "configuration": {
        "servedModelName": "support-llm",                     # the `model` value callers pass
        "maxNumberOfSequences": 8,                            # parallel requests
        "tensorParallelism": 1,                               # GPUs to split the model across
        "vllmArguments": "--enable-auto-tool-choice --tool-call-parser hermes",
    },
    "generalAccess": "Restricted",                            # Restricted | Viewer | Consumer
    "collaborators": [{"userId": "<user-id>", "name": "<username>"}],   # or {"organizationId": ..., "name": ...}
    "versionLabel": "v1",
}
endpoint = requests.post(f"{base_url}/api/gen-ai/beta/endpoints", headers=headers, json=body).json()
endpoint_id = endpoint["id"]
```

Field notes, from the spec:

- `configuration.servedModelName` is the name callers use as `model` in OpenAI-style requests.
- `configuration.maxNumberOfSequences` is the number of requests processed in parallel; `tensorParallelism` is the number of GPUs the model is split across.
- `configuration.vllmArguments` is the string passed to the vLLM binary. Tool calling with agent frameworks needs `--enable-auto-tool-choice --tool-call-parser hermes` for some models.
- `modelSource.huggingFace.modelType` is one of `LLM`, `Embedding`, `OtherGenAI`.
- `generalAccess` is one of `Restricted`, `Viewer`, `Consumer`; `collaborators` entries carry either a `userId` or an `organizationId` plus `name`.
- `vanityUrl` is optional; check availability first with the vanity-url route. Response `vanityUrl` and `url` are both returned on the endpoint.
- `GET /api/gen-ai/beta/default-endpoint-environment` returns `{"id", "name"}` and optionally `"revisionId"` (the Domino vLLM Environment). Pass `id` as `environment.environmentId`; `environment.revisionId` is optional in the create body and the default-environment response may omit it. Verified against the 6.3.1 and 6.4.0 specs and a live Cloud deployment (2026-09-28).

## Wait for it to run, then get the URL

```python
import time

for _ in range(120):
    ep = requests.get(f"{base_url}/api/gen-ai/beta/endpoints/{endpoint_id}", headers=headers).json()
    status = ep["currentVersion"]["status"]
    if status in ("Running", "Failed", "BuildFailed"):
        break
    time.sleep(10)

print(status, ep["url"])   # ep["url"] is the base_url for OpenAI-style clients
```

`currentVersion.status` is one of `Building`, `BuildFailed`, `Starting`, `Running`, `Stopping`, `Stopped`, `Failed`, `Unknown`. On `Failed` or `BuildFailed`, read `realTimeLogs` for the version before retrying. The endpoint detail also carries `requestCount`, `instructions`, `generalAccess`, `project`, and `currentVersion.hardwareTier` (with the data plane it runs on).

## Call the running endpoint

Use `ep["url"]` as `base_url` and `configuration.servedModelName` as `model`; the bearer is the in-run access token (or a PAT outside a run). See SKILL.md "Step 3: call the endpoint". Predictions go to the endpoint URL, not to `/api/gen-ai/beta/...`, which is management only.

## Stop, start, update, delete

```python
v = ep["currentVersion"]["number"]
requests.post(f"{base_url}/api/gen-ai/beta/endpoints/{endpoint_id}/versions/{v}/stop", headers=headers)
requests.post(f"{base_url}/api/gen-ai/beta/endpoints/{endpoint_id}/versions/{v}/start", headers=headers)

# change the hardware tier or vLLM arguments of a version
requests.patch(f"{base_url}/api/gen-ai/beta/endpoints/{endpoint_id}/versions/{v}", headers=headers,
               json={"hardwareTierId": "gpu-a100-40gb",
                     "configuration": {"vllmArguments": "--max-model-len 8192"}})

requests.delete(f"{base_url}/api/gen-ai/beta/endpoints/{endpoint_id}", headers=headers)
```

After a stop or delete, `GET` the endpoint again and confirm the state before assuming the operation completed.

## Metrics and logs

```python
params = {"startTime": "2026-09-01T00:00:00Z", "endTime": "2026-09-28T00:00:00Z", "aggregationWindow": "1h"}
base = f"{base_url}/api/gen-ai/beta/endpoints/{endpoint_id}/versions/{v}"
requests.get(f"{base}/request-metrics", headers=headers, params=params).json()
requests.get(f"{base}/vllm-token-metrics", headers=headers, params=params).json()
requests.get(f"{base}/vllm-latency-metrics", headers=headers, params=params).json()
requests.get(f"{base}/pod-resource-metrics", headers=headers, params=params).json()
requests.get(f"{base}/realTimeLogs", headers=headers, params={"limit": 200}).json()
```

The accepted values of `aggregationWindow` and `logType` are defined by the deployment's spec; read them from `public-api.json` rather than guessing.
