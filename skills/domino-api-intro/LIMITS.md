# Limits, pagination, and deprecated patterns

Auth for supported methods only: https://docs.domino.ai/cloud/reference/api/domino-api-authentication (proxy, PAT, SA). Error handling: [ERRORS.md](./ERRORS.md).

Legacy user API keys are described as deprecated, never recommended. Do not use them in new skill examples or agent steps:

- `X-Domino-Api-Key` header
- `DOMINO_USER_API_KEY` (even if injected in a run)
- Public deployment URL + user/owner API key
- JWT `iss` scraping to discover cluster URL (use explicit public URL, forwarded headers, or env you control)

Legacy API key docs (migration only): https://docs.domino.ai/cloud/reference/api/domino-api-authentication#authenticate-with-an-api-key-legacy

## Deprecated env names (still work; prefer canonical)

| Deprecated | Prefer |
|------------|--------|
| `DOMINO_API_HOST` in run code | `DOMINO_USER_HOST` (same HTTP base for platform APIs) |

## Pagination and list caps

Many list APIs accept `offset` and `limit` and return `totalCount`. Treat responses as **possibly incomplete**:

- Some list endpoints cap page size (often around **100** rows) regardless of a larger `limit`.
- Some routes ignore `offset` or filter query params; client-side filter may be required.
- A first page with `data.length < totalCount` means you must paginate or accept partial results.

Dataset v2 listing is a common case: see [datasets](../datasets/SKILL.md) and [API-DATASETS](../python-sdk/API-DATASETS.md).

Governance bulk operations (recertification, bundle lists): paginate with offset/limit until no more rows.

## Bulk download vs paginated events

Prefer paginated event APIs over single responses that load entire audit or export payloads. Large one-shot downloads often return **502** or timeout; see [ERRORS.md](./ERRORS.md).

## Async job start

Job and run starts usually return the run id in the **JSON body**, not only a `Location` header. Poll until terminal status; field names vary (`status`, `statusName`, nested execution status). See [ERRORS.md](./ERRORS.md) and [jobs](../jobs/SKILL.md).

## Platform-only legacy JWT tooling

`DOMINO_TOKEN_FILE` and related legacy JWT file tooling (feature off by default): do not use in new automation. Prefer API proxy or PAT/SA.
