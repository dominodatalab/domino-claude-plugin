---
name: domino-model-serving
description: Deploy, invoke, and retire Domino model APIs and registered models via REST. Covers modelServing lifecycle, registered-models v1 vs v2 paths, MLflow tracking vs registry API, inference URLs vs management API, and GenAI endpoint vanity URLs. Use when automating model deployment, predictions, registry updates, or debugging stop/archive/delete behavior.
---

# Domino model serving (REST)

Programmatic model deployment and inference on Domino. UI-focused endpoint monitoring stays in [model-endpoints](../model-endpoints/SKILL.md). Shared REST field catalogs live in [API-MODEL-SERVING.md](../python-sdk/API-MODEL-SERVING.md) and [API-MODELS.md](../python-sdk/API-MODELS.md).

Authentication: https://docs.domino.ai/cloud/reference/api/domino-api-authentication . **Do not use API keys.**

## Configuration

| Context | Base | Authorization |
|---------|------|----------------|
| In-run, `DOMINO_API_PROXY` set | `{DOMINO_API_PROXY}` | None |
| In-run, no proxy | `{DOMINO_USER_HOST or DOMINO_API_HOST}` | Bearer from `http://localhost:8899/access-token` |
| Outside run | Public deployment URL | Bearer PAT or SA |

Management paths include `/api/modelServing/v1/...`, `/api/registeredmodels/v1|v2/...`. Confirm with `GET {base}/api/modelServing/v1/modelApis?limit=1` returning HTTP 200.

```bash
curl ${TOKEN:+-H "Authorization: Bearer $TOKEN"} "$BASE/api/modelServing/v1/modelApis?limit=1"
```

## Three surfaces (do not merge)

| Surface | Purpose |
|---------|---------|
| **Model Serving REST** | `/api/modelServing/v1/modelApis` deploy, versions, lifecycle |
| **Registered models REST** | `/api/registeredmodels/v2` list/register; `/api/registeredmodels/v1/{modelName}` get/update/versions |
| **MLflow tracking** | `MLFLOW_TRACKING_URI` / runs UI; not the same as registered-models REST |

Logging a run to MLflow does not replace registry or modelServing calls for deployment automation.

## Management vs inference URL

- Create/list/update: platform base + `/api/modelServing/v1/...` (or registered-models paths).
- **Predict:** use the **`url`** field on the model API or version (often `.../models/.../latest/model`), on the deployment ingress. That path is not routed through `DOMINO_API_HOST` sidecar the same way as `/api/`.

GenAI: management API vs `https://.../endpoints/{vanity}` split. See `doc-examples/python/list_genai_endpoints_and_call.py`.

## Lifecycle (model APIs)

Typical order:

1. Train / register (MLflow and/or `POST /api/registeredmodels/v2/...`).
2. `POST /api/modelServing/v1/modelApis` (or new version on existing API).
3. Poll `GET /api/modelServing/v1/modelApis/{modelApiId}` until `status` is `Running` (or `Failed`); then read **`url`** for invoke.
4. **Stop** vs **archive** vs **delete** are different product operations; names and reliability differ by route.
5. Treat **DELETE** on deployments/model APIs as best-effort; verify resource gone before assuming cleanup.
6. **Stop** may be long-running and not idempotent; poll status instead of fire-and-forget retry loops.

Details and route list: [API-MODEL-SERVING.md](../python-sdk/API-MODEL-SERVING.md).

## Registered model path key

`modelName` in `/api/registeredmodels/v1/{modelName}` is the **registered model name string**, not an opaque UUID. List/register often use **v2**; get/update/versions use **v1** with that name in the path.

## Invocation auth

Use the model API token documented on https://docs.domino.ai for the model endpoint invoke path. Older examples may show a basic-auth pattern with the token as both user and password; treat that as legacy and confirm on your cluster swagger before hardcoding.

## Related documentation

- [API-MODEL-SERVING.md](../python-sdk/API-MODEL-SERVING.md) - REST lifecycle and routes
- [API-MODELS.md](../python-sdk/API-MODELS.md) - broader models API catalog
- [model-endpoints](../model-endpoints/SKILL.md) - Grafana, Triton, UI deploy
- Model registry (product): https://docs.domino.ai/cloud/platform-capabilities/features/model-registry
