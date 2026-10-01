---
name: domino-api-intro
description: Introduction to calling Domino platform APIs. Covers authentication (API proxy, PAT, service account), which host to use for which API, pagination limits, and common errors. Use before any other Domino API, SDK, app, extension, or governance automation skill.
compatibility: Domino 6.3 and Domino Cloud. Requires DOMINO_API_HOST; in a run use DOMINO_API_PROXY or the localhost:8899 access-token endpoint, outside a run a Personal Access Token.
---

# Domino platform API intro

Applies to Domino 6.3 and Domino Cloud.

Read this skill first whenever you automate Domino over HTTP or the Python SDK.

## Authentication

Follow https://docs.domino.ai/cloud/reference/api/domino-api-authentication for every call (API proxy in-run, access token + platform host, PAT, and service account).

Legacy user API keys (`X-Domino-Api-Key`, `DOMINO_USER_API_KEY`) are described as deprecated, never recommended. Product migration docs: https://docs.domino.ai/cloud/reference/api/domino-api-authentication#authenticate-with-an-api-key-legacy

| Context | Summary (details on the auth page) |
|---------|-------------------------------------|
| In-run | Prefer `DOMINO_API_PROXY` with **no** `Authorization` header when set; else Bearer from `http://localhost:8899/access-token` on `DOMINO_USER_HOST` (or `DOMINO_API_HOST`) |
| Outside a run | Public deployment HTTPS URL + Bearer **PAT** (you) or **service account** (automation) |

Host selection (gateway, governance 404, WebVFS, inference) is separate from auth mode: [HOSTS.md](./HOSTS.md).

## Reference files (this skill)

| File | Use when |
|------|----------|
| [HOSTS.md](./HOSTS.md) | Pick base URL (gateway, WebVFS, inference, governance external URL) |
| [LIMITS.md](./LIMITS.md) | Pagination, caps, deprecated env names |
| [ERRORS.md](./ERRORS.md) | Retries, 502/timeouts, job status fields, datasource 500 workaround |
| [SDK-MAP.md](./SDK-MAP.md) | Which plugin skill or doc covers each surface |
| [API-SPECS.md](./API-SPECS.md) | OpenAPI files and route discovery |

## Next steps

Use domain skills under `skills/` (python-sdk, apps, governance, datasets, and others). They assume the auth and host rules above.
