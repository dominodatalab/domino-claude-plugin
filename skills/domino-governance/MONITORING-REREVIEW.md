# Monitoring-driven re-review

Validator and approver handle a drift or monitor finding on an existing production bundle: bundle reopens, new evidence against current policy, re-approval, close finding, bundle back to approved.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
POST /findings {**drift_finding, "bundleId": bundle_id}
# required: approver, assignee, bundleId, name, policyVersionId, severity

POST /rpc/submit-result-to-policy {"bundleId": bundle_id, "policyId": policy_id, **new_evidence}

POST /rpc/compute-policy {"bundleId": bundle_id, "policyId": policy_id}
# poll GET /results/latest?bundleID=bundle_id (SKILL.md)

POST /rpc/publish-approval-event {**approval_event, "bundleId": bundle_id}

PUT /findings/{finding_id} {"status": "Done"}

GET /bundles/{bundle_id}/findings
# confirm no open findings (status not Done / WontDo)
```

## Gotchas

- Reopening a bundle does not detach old evidence.
- Policy may have been version-bumped; recompute against the version in effect at the new submission, not the original.
- Monitor finding source is a separate service.
