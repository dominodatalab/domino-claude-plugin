# Apps REST API (automation)

Agent reference for Domino Apps **management** APIs. Container layout, `app.sh`, and proxy UI behavior stay in [SKILL.md](./SKILL.md).

Authentication: https://docs.domino.ai/cloud/reference/api/domino-api-authentication . **Do not use API keys.**

## Configuration

Platform apps management routes live under `/api/apps/v1` and `/api/apps/beta`. Base URL resolution matches other platform APIs:

| Context | Base | Authorization |
|---------|------|----------------|
| In-run, `DOMINO_API_PROXY` set | `{DOMINO_API_PROXY}` | None (proxy adds JWT) |
| In-run, no proxy | `{DOMINO_USER_HOST or DOMINO_API_HOST}` | Bearer from `GET http://localhost:8899/access-token` |
| Outside run or unreachable sidecar | `{public deployment URL}` | Bearer PAT or SA |

Prefix paths onto that base, e.g. `{base}/api/apps/v1/apps`. Confirm with `GET {base}/api/apps/v1/apps?limit=1` returning HTTP 200 before longer workflows.

```bash
curl ${TOKEN:+-H "Authorization: Bearer $TOKEN"} "$BASE/api/apps/v1/apps?limit=1"
```

## v1 vs beta

| Use | Path prefix | Notes |
|-----|-------------|--------|
| **Prefer for automation** | `/api/apps/v1` | Create app, publish, versions, `start` / `stop`, delete app |
| **Legacy / read-only runtime** | `/api/apps/beta` | List/filter in older examples; **instance logs**, `realTimeLogs`, **views**, list running instances, instance DELETE |

Do not build new write flows on beta when a v1 equivalent exists. Beta list responses may omit fields needed for publish/version chains.

**Rule:** v1 for create, publish, start, stop. Beta for streaming logs, views, and instance telemetry only.

## Publish chain (v1)

Typical automation sequence:

1. `POST /v4/jobs/{projectId}/resolveJobDefaults` with `commandToRun` matching the app entry (yields `environmentId`, `hardwareTierId`).
2. `POST /api/apps/v1/apps` with `projectId`, `name`, `entryPoint`, `initialVersion` (environment + hardware tier from defaults).
3. Optional: `POST /api/apps/v1/apps/{appId}/publish` when promoting drafts (draft-to-published flows).
4. `POST /api/apps/v1/apps/{appId}/versions/{versionId}/start` to run.
5. `POST /api/apps/v1/apps/{appId}/versions/{versionId}/stop` to stop.

Alternate one-shot: `POST /api/apps/v1/apps/{appId}/versions/createAndStart`.

Reference implementation: `doc-examples/python/app_publish_chain.py` in the api-improvements repo (resolve defaults, `POST /api/apps/v1/apps`, `.../start`).

Product docs: https://docs.domino.ai/cloud/platform-capabilities/features/apps

## Management API vs user-facing app URL

- **Management** (list, start, stop, versions): `{platform base}/api/apps/v1/...` through the platform API gateway or proxy.
- **User opens the app** in a browser: URL on the deployment or data-plane ingress (often in the app resource `url` field), not the same path as `/api/apps/...`.

Do not call management routes on the public app hostname or vice versa.

## GenAI / inference vanity URLs (related)

Model and GenAI **inference** is not on the platform gateway. Management may be `/api/gen-ai/beta/endpoints` (or similar) while invoke uses `https://{data-plane or apps host}/endpoints/{vanity}` from the endpoint record.

`DOMINO_API_HOST` alone does not construct a working inference URL. Read `url` / vanity from the management API response and call that host for predictions.

Reference: `doc-examples/python/list_genai_endpoints_and_call.py` (api-improvements, rank 12).

## When deploy or start is blocked

Separate causes (do not conflate):

| Symptom | Likely layer |
|---------|----------------|
| HTTP 403 on apps API | Project **RBAC** or token scope |
| Admin-only setting | **Central config** / feature flags (admin APIs) |
| Hardware tier, quota, spot/GPU policy | Platform **policy** or tier gates (UI often shows more detail than API) |
| Model governance bundle not approved | **Governance** gates (`GET /api/governance/v1/bundles/{id}` and bundle gates), not apps RBAC |

Governance gate coarse-graining on `GET /bundles/{id}/gates` is a **governance** concern, not an apps beta/v1 route issue.

## Swagger

In-run: `GET $DOMINO_API_HOST/assets/public-api.json` (Apps tags). Confirm field names on the cluster before codegen.

```bash
curl ${TOKEN:+-H "Authorization: Bearer $TOKEN"} "$DOMINO_API_HOST/assets/public-api.json"
```

OpenAPI paths include `/api/apps/v1/apps`, `.../publish`, `.../versions/{versionId}/start`, `.../stop`, and beta instance/log routes under `/api/apps/beta/...`.
