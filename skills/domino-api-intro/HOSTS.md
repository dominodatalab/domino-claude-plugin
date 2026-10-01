# How to reach Domino HTTP endpoints

Authentication: https://docs.domino.ai/cloud/reference/api/domino-api-authentication .

In-run: `DOMINO_API_PROXY` with **no** `Authorization` header when that works, else `DOMINO_USER_HOST` / `DOMINO_API_HOST` + Bearer from `http://localhost:8899/access-token`. Outside a run: **public deployment HTTPS URL** + PAT or SA. Legacy user API keys are described as deprecated, never recommended.

## Outside any Domino run (external access)

| What to set | Value |
|-------------|--------|
| Base URL | Public deployment URL (what users open in the browser), e.g. `https://yourcompany.domino.ai` |
| Credential | Bearer PAT (you) or service account token (automation) |


## In-run: two layers (routing + auth)

**Routing:** Most control-plane paths go on **`DOMINO_USER_HOST`** when the platform API gateway is on, or on the legacy sidecar base when it is off. Some paths (governance when gateway is off, WebVFS, inference) use a **different** base; see below.

**Auth:** Prefer **`DOMINO_API_PROXY`** (JWT credential propagation, common on Domino 5.4.0+ when your admin enabled it). The proxy URL is for **auth**, not a substitute for knowing whether a path is registered on the gateway. If the proxy is unset, use access-token + `DOMINO_USER_HOST`. Details: auth page above.

**Canonical host name:** use **`DOMINO_USER_HOST`**. **`DOMINO_API_HOST`** is the same base in runs; treat it as a deprecated alias.

**Sanity check:** confirm paths against https://docs.domino.ai/llms-full.txt before calling an endpoint you have not used on this cluster.

## Platform API gateway (routing through port 8763)

The **platform API gateway** (`operations-api-gateway-service`) registers selected routes so user code can call them on one local HTTP listener instead of many legacy localhost ports.

### When the gateway is ON

All of the following must be true (typical modern local data-plane runs):

| Requirement | Meaning |
|-------------|---------|
| Feature flag **`ApiGateway.UserCodeLocalDpEnabled`** | Enabled in central config (available since Domino 6.3; default off until your admin turns it on) |
| Run on **local control-plane data plane** | Remote data-plane runs may not get gateway wiring even if the flag is on elsewhere |

When ON, Domino injects roughly:

| Variable | Typical value | Use |
|----------|---------------|-----|
| `DOMINO_USER_HOST` | `http://127.0.0.1:8763` | Prefix for gateway-registered platform paths |
| `DOMINO_API_HOST` | same | Deprecated alias of `DOMINO_USER_HOST` |
| `DOMINO_DATASOURCE_PROXY_HOST` | `http://127.0.0.1:8763` | Datasource HTTP on gateway listener |
| `DOMINO_DATASOURCE_PROXY_FLIGHT_HOST` | `grpc://127.0.0.1:8764` | Datasource gRPC |
| `MLFLOW_TRACKING_URI` | `http://127.0.0.1:8763` | MLflow tracking |
| `DOMINO_DATA_API_GATEWAY` | `http://127.0.0.1:8763/vectordb` | Vector DB path |
| `DOMINO_MLFLOW_DEPLOYMENTS` | `http://127.0.0.1:8763/mlflow-deployments` | MLflow deployments path |

Example call (gateway ON, path registered on gateway):

```bash
curl "$DOMINO_USER_HOST/v4/users/self" -H "Authorization: Bearer $(curl -s http://localhost:8899/access-token)"
```

With `DOMINO_API_PROXY` set and routing working for that path:

```bash
curl "$DOMINO_API_PROXY/v4/users/self"
```

Whether a **specific** path is on 8763 varies by Domino version and gateway registration. If you get **404** on `DOMINO_USER_HOST`, the path may be legacy-only, external-only, or on another host env var.

### When the gateway is OFF

Feature flag off and/or remote data plane: **`DOMINO_USER_HOST`** often points at a **nucleus-internal** sidecar base, **not** `127.0.0.1:8763`. MLflow, vector DB, and datasource may use **separate** localhost ports (8766-8768) instead of 8763.

| Variable | Typical role when gateway OFF |
|----------|-------------------------------|
| `DOMINO_USER_HOST` / `DOMINO_API_HOST` | Legacy platform sidecar (many `/v4` routes) |
| `MLFLOW_TRACKING_URI`, `DOMINO_DATA_API_GATEWAY`, `DOMINO_MLFLOW_DEPLOYMENTS` | Separate legacy listeners |
| `DOMINO_DATASOURCE_PROXY_*` | Direct datasource proxy, not unified on 8763 |

Many **`/api/*`** routes were **never** on the legacy sidecar. A **404** on the sidecar does not always mean the path is wrong globally; try the public deployment URL with Bearer PAT/SA (see governance below).

### Paths that usually need a different base (even when gateway is ON)

| Need | Env / source (not `DOMINO_USER_HOST` alone) |
|------|---------------------------------------------|
| WebVFS file ops | Data-plane `/webvfs/...` host (see netapp-volumes skill) |
| Inference predict | `url` / vanity from management API response |
| Remote filesystem volume admin | `DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT` |

## Governance: `/api/governance/v1`

Governance (guardrails) always uses the suffix **`/api/governance/v1`** on whatever base works. Pick the base where **`GET .../policy-overviews` returns HTTP 200**. Try in order; stop at the first success.

Auth: https://docs.domino.ai/cloud/reference/api/domino-api-authentication . Workflow detail: [domino-governance](../domino-governance/SKILL.md).

### Gateway ON (governance registered on 8763)

When `ApiGateway.UserCodeLocalDpEnabled` is on and governance is registered on the platform gateway, **`DOMINO_USER_HOST`** can reach governance like other `/api/*` routes.

| Try | Base | Authorization |
|-----|------|----------------|
| 1 | `{DOMINO_API_PROXY}/api/governance/v1` | None (proxy adds JWT) when `DOMINO_API_PROXY` is set |
| 2 | `{DOMINO_USER_HOST or DOMINO_API_HOST}/api/governance/v1` | Bearer from `http://localhost:8899/access-token` |

```bash
GOV="/api/governance/v1"
# 1) Proxy (preferred when DOMINO_API_PROXY is set)
curl -s "$DOMINO_API_PROXY$GOV/policy-overviews"
# 2) Platform gateway (no proxy)
curl -s "$DOMINO_USER_HOST$GOV/policy-overviews" \
  -H "Authorization: Bearer $(curl -s http://localhost:8899/access-token)"
```

If step 1 or 2 returns **404**, governance is not on the sidecar/gateway for this deployment; use the gateway OFF path below even if other routes work on 8763.

### Gateway OFF (or governance 404 on `DOMINO_USER_HOST`)

Guardrails is often reachable only on the **public deployment ingress**, not on nucleus-internal.

| Context | Base | Authorization |
|---------|------|----------------|
| In-run, 404 on proxy and `DOMINO_USER_HOST` | `{public deployment URL}/api/governance/v1` | Bearer PAT or SA |
| Outside any run | `{public deployment URL}/api/governance/v1` | Bearer PAT or SA |

Domino does **not** inject `DOMINO_EXTERNAL_URL`. Set it yourself or derive the public host from:

| Source | Notes |
|--------|--------|
| `DOMINO_EXTERNAL_URL` | If you define it in the run or app |
| `X-Forwarded-Host` + `X-Forwarded-Proto` | Apps/workspaces behind ingress |
| `VSCODE_PROXY_URI` | Workspaces (parse hostname) |
| `DOMINO_PUBLIC_HOST` / `DOMINO_EXTERNAL_HOST` | App/extension conventions |

Do not scrape JWT `iss` to discover the cluster URL.

```bash
BASE="https://your-deployment.domino.tech/api/governance/v1"
curl -s "$BASE/policy-overviews" -H "Authorization: Bearer $PAT_OR_SA"
```

## Executor vs notebook (one pitfall)

On **executors**, `DOMINO_USER_HOST` can mean the public `dominoUrl`. In **user code inside the run container**, it means the in-pod sidecar/gateway base. Do not copy executor env into notebook API examples.

## Related

- [LIMITS.md](./LIMITS.md) legacy API key guidance and pagination
- [ERRORS.md](./ERRORS.md) 404 and retry behavior
- [API-SPECS.md](./API-SPECS.md) for OpenAPI files and route discovery
