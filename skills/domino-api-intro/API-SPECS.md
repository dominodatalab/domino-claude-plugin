# OpenAPI specs

## Public routes

Use for `/api/*` (v1, beta, governance, taxonomy, apps, jobs, model serving, and the rest of the published catalog).

| What | URL |
|------|-----|
| Index | https://docs.domino.ai/llms-full.txt |
| Short index | https://docs.domino.ai/llms.txt |
| OpenAPI JSON | https://docs.domino.ai/api-specs/cloud/public-api.json |
| Reference UI | https://docs.domino.ai/cloud/reference/api/domino-open-api |

## Governance results (public catalog)

Paths below are under `/api/governance/v1` on the governance base from [domino-governance SKILL](../domino-governance/SKILL.md#configuration). They are in [public-api.json](https://docs.domino.ai/api-specs/cloud/public-api.json).

| Route | Notes |
|-------|--------|
| `GET /api/governance/v1/results` | ListResults. Required query `bundleID`. Optional `policyID`, `policyVersionID`, `artifactID`, `offset`, `limit`. Response uses `data` and `meta.pagination`. |
| `GET /api/governance/v1/results/latest` | Latest artifact results for a bundle. Required query `bundleID`. |

## Internal routes (v4-style)

Use for legacy nucleus paths in the internal spec (for example `/jobs/...`, `/runs/...`, `/environments/...`).

| What | In a run | Anywhere |
|------|----------|----------|
| OpenAPI JSON | `$DOMINO_API_HOST/assets/swagger.json` | `https://<deployment-url>/assets/swagger.json` |
| Swagger UI | `$DOMINO_USER_HOST/assets/lib/swagger-ui/index.html?url=/assets/swagger.json` | `https://<deployment-url>/assets/lib/swagger-ui/index.html?url=/assets/swagger.json` |

## By area

| Area | Where to look |
|------|----------------|
| Apps, jobs, model serving, gen-ai, extensions, governance, taxonomy, projects, datasets, environments | Public routes section |
| Governance bundle results (ListResults) | [Governance results (public catalog)](#governance-results-public-catalog) |
| Legacy `/v4` and internal-only paths | Internal routes section |
