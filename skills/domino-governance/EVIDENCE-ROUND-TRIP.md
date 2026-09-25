# Evidence round-trip with findings

Submitter and reviewer cycle: compute-policy, submit result, reviewer opens a finding, submitter resolves with new evidence, recompute, close finding, advance stage.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
POST /rpc/compute-policy {"bundleId": bundle_id, "policyId": policy_id}
# poll: GET /results/latest?bundleID=bundle_id until needed artifacts have isLatest=true
# see SKILL.md "After compute-policy (polling)"

POST /rpc/submit-result-to-policy {"bundleId": bundle_id, "policyId": policy_id, **submit_body}

POST /findings {
    "bundleId": bundle_id,
    "policyVersionId": policy_version_id,
    "name": "...",
    "severity": "...",
    "approver": {...},
    "assignee": {...},
    **optional_fields,
}

POST /rpc/submit-result-to-policy {"bundleId": bundle_id, "policyId": policy_id, **resolve_body}

POST /rpc/compute-policy {"bundleId": bundle_id, "policyId": policy_id}
# poll results/latest again

PUT /findings/{finding_id} {"status": "Done"}

POST /rpc/publish-approval-event {**approval_event, "bundleId": bundle_id}
PATCH /bundles/{bundle_id} {"stage": next_stage_name}
# when policy requires explicit stage name after approvals

GET /bundles/{bundle_id}/findings
# open = status not Done and not WontDo; resolve before advancing
```

## Gotchas

- Poll `GET /results/latest?bundleID=...` after each compute-policy (see SKILL.md).
- Findings can open at bundle level or per evidence stage.
- Resolving a finding requires a new submission and recompute; PUT status alone is not enough for audit meaning.
- Do not advance while open findings remain on the stage.
