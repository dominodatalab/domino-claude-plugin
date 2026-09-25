# Model serving REST (agent reference)

Deep reference for `/api/modelServing/v1` and registered-models paths. Orientation and pitfalls: [domino-model-serving/SKILL.md](../domino-model-serving/SKILL.md).

Authentication: https://docs.domino.ai/cloud/reference/api/domino-api-authentication . In-run prefer `DOMINO_API_PROXY` (no header) or `DOMINO_USER_HOST` + access-token; outside run use public URL + PAT/SA.

## Registered models v1 vs v2

| Operation | Path | Notes |
|-----------|------|--------|
| List / register (bulk) | `/api/registeredmodels/v2/...` | Prefer for discovery and create |
| Get / update / versions | `/api/registeredmodels/v1/{modelName}/...` | Path key is **model name**, not id |

Both may appear in swagger; do not assume one base path for all registry operations.

## Model Serving (`/api/modelServing/v1`)

Common flow:

```
POST /api/modelServing/v1/modelApis
GET  /api/modelServing/v1/modelApis/{modelApiId}
POST /api/modelServing/v1/modelApis/{modelApiId}/versions
GET  /api/modelServing/v1/modelApis/{modelApiId}/versions/{modelApiVersionId}
```

Use response fields `url`, `status`, and version ids for invoke and polling. Async batch predict uses `/api/modelApis/async/v1/...` (separate from synchronous `url` invoke).

## Lifecycle pitfalls

- **Stop**, **archive**, and **delete** are not interchangeable; wrong verb leaves billable or stale resources.
- **Deployment delete** has been unreliable in the field; after DELETE, GET the resource or list endpoints to confirm removal.
- **Stop** can be async and non-idempotent; repeated stop without checking status may confuse automation.
- **Service account auth** may fail on some modelServing routes on remote data planes while PAT works; test the identity you automate with.

Treat these as product bugs to work around; do not assume a fix when automating.

## MLflow vs REST

| Need | Use |
|------|-----|
| Experiment tracking, run artifacts | `MLFLOW_TRACKING_URI`, MLflow client |
| Registry record, governance attachments | `/api/registeredmodels/...` |
| Hosted prediction endpoint | `/api/modelServing/v1/modelApis` + inference `url` |

MLflow proxy/monitoring specs are not a substitute for registered-models or modelServing OpenAPI.

## GenAI endpoints

List/create: GenAI management routes under `/api/gen-ai/...` (beta in many deployments). Invoke: vanity URL on data-plane/apps host (`/endpoints/{vanity}`), not `DOMINO_API_HOST/api/...`.

Example: `doc-examples/python/list_genai_endpoints_and_call.py`.

## Calling predictions

1. Deploy or fetch model API; read **`url`** from GET response.
2. POST to that **url** with auth required by that endpoint (verify on cluster; see API-MODELS.md invoke section).
3. Do not POST predictions to `/api/modelServing/v1/modelApis/{id}` unless swagger documents that route for invoke.

## Swagger

`GET $DOMINO_API_HOST/assets/public-api.json` - ModelAPI, ModelAPIVersion, RegisteredModels tags. Field names vary by release; verify before agents generate clients.

```bash
curl ${TOKEN:+-H "Authorization: Bearer $TOKEN"} "$DOMINO_API_HOST/assets/public-api.json"
```

Product: https://docs.domino.ai/cloud/reference/api/domino-open-api
