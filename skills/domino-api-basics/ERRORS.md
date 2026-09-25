# Errors and retries (agents)

How to interpret Domino API failures, when to retry, and when to change approach. Pagination caps and list quirks live in [LIMITS.md](./LIMITS.md) (same skill dir). Auth mistakes look like 401/403; see https://docs.domino.ai/cloud/reference/api/domino-api-authentication .

Broader API discovery: https://docs.domino.ai/llms-full.txt

Example scripts with inline handling: `doc-examples/python/` in the api-improvements repo (`run_job_and_poll.py`, `list_datasets_v2.py`, `datasource_list_and_query.py`).

## Structured error bodies

Many platform routes return a JSON error envelope (API Standard):

```json
{
  "message": "Human-readable summary",
  "errors": [
    {"code": "...", "message": "...", "details": [{"field": "...", "message": "..."}]}
  ]
}
```

On 4xx, read `errors[].code` and `errors[].message` before retrying. On opaque 500 with HTML or empty body, treat as infrastructure or bug, not a validation fix.

## HTTP status: retry or not

| Code | Agent action |
|------|----------------|
| **400** | Fix request body, path, or query. Do not blind retry. |
| **401** | Wrong or expired token, or missing proxy/auth mode. Refresh PAT, use access-token in-run, or use proxy without duplicate Bearer. Do not retry until auth is fixed. |
| **403** | RBAC or policy block. Retrying the same call will not help; change role, project, or resource. |
| **404** | Wrong id, wrong API base (sidecar vs public URL vs data-plane host), or route not on this gateway. Fix host/path; see domain skills (WebVFS, governance external URL, inference vanity URL). |
| **409** | Conflict (duplicate name, state). Back off or fetch current state and reconcile. |
| **502 / 504 / timeout** | Often payload too large or upstream overload. Shrink request, paginate, or use a tier-2 API (see datasource audit below). Limited retries with backoff only if the operation is idempotent and size is already reduced. |
| **500** | May be transient or a known backend bug. Retry once with backoff only if the operation is idempotent and docs do not mark the route as broken. Otherwise stop and surface the error. |

## Scale and list failures

Large list or export calls that build one huge response often fail with **502** or timeout. Prefer paginated endpoints (`offset`/`limit`, `pageToken`, or domain-specific event APIs) over "download everything" routes.

If a list returns fewer rows than `totalCount` or ignores filters, assume truncation or ignored query params; do not treat the first page as complete. Details: [LIMITS.md](./LIMITS.md).

## Jobs and execution status

Job poll responses may expose status under different fields (`status`, `statusName`, nested `statuses.executionStatus`). Normalize before comparing to terminal values (`Succeeded`, `Failed`, `Stopped`, `Error`, `Cancelled` / `Canceled`).

Missing or stale status while a run is still active: keep polling with backoff; do not assume failure from an empty status field alone.

Async job start returns the run id in the **response body**, not only a `Location` header. Poll `GET /v4/jobs/{runId}` (or the route your swagger documents for that start path).

Reference: `doc-examples/python/run_job_and_poll.py`.

## Datasource audit and legacy DataSet projects

**Do not retry** datasource automation that hits **500** on legacy DataSet project paths when listing or bulk audit download. That pattern is a known backend limitation, not a transient glitch.

Workarounds:

- List datasources: `GET /api/datasource/v1/datasources` (filter client-side by project if needed).
- Audit at scale: paginated `GET /v4/datasource/audit/events` (not a single bulk dump that loads the full audit in one response).

Reference: `doc-examples/python/datasource_list_and_query.py`.

## Wrong surface symptoms

These often look like 404 or connection errors, not JSON `ErrorResponse`:

- WebVFS file ops through `DOMINO_API_HOST` only (need data-plane `/webvfs/...` host).
- Governance on run sidecar when gateway is off (need public URL + Bearer).
- Inference or GenAI predict on management API base (use `url` / vanity from the management response).

Fix the base URL and auth mode before retrying.

## Safe 4xx handling for agents

- Do not escalate 403 into "try API key" or scrape JWT claims for hostnames.
- Do not retry POST creates on 400 hoping the server accepts a second shape; read the error body and fix fields.
- After a failed deploy/start (apps, model APIs, jobs), GET the resource state before issuing the same POST again.
