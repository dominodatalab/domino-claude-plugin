# Read governance context for downstream use

Agent or extension, given a modelId or bundleId, lists bundles, computes policy, waits for latest results, gets findings, and returns structured context for an LLM, dashboard, or report.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
GET /bundles?projectId={project_id}&offset={offset}&limit={limit}

# Filter by bundle_id, or by registered_model_name on attachments:
#   a["type"] == "ModelVersion" and a["identifier"]["name"] == registered_model_name

# Per matching bundle:
POST /rpc/compute-policy {"bundleId": bundle_id, "policyId": policy_id}
GET /results/latest?bundleID={bundle_id}
# poll until artifacts you expose have isLatest=true (SKILL.md)

GET /bundles/{bundle_id}/findings
```

## Gotchas

- Only `isLatest=true` results count as evidence; drafts are noise.
- Multi-bundle per model means return all matches, not first.
- Base URL and auth: try proxy (no header), then in-run `DOMINO_USER_HOST` + access-token, then public URL + PAT if `GET $BASE/policy-overviews` returns HTTP 404 ([SKILL.md](./SKILL.md#configuration)).
