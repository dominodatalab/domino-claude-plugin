# Approval gate

Use when implementing approver automation: list pending approvals on the bundle, download the bundle report PDF, review attachments and evidence, publish an approval event, optionally set the primary stage on the bundle, and verify the stage actually changed.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
GET /bundles/{bundle_id}
# record bundle["stage"] as before_stage

GET /bundles/{bundle_id}/report
# response body is application/pdf (binary), not JSON

POST /rpc/publish-approval-event {
    "bundleId": bundle_id,
    "policyId": policy_id,
    "projectId": project_id,
    "eventType": "RequestApproved",  # or RequestRejected, etc.
    "approvalId": approval_id,
}

PATCH /bundles/{bundle_id} {"stage": next_stage_name}
# only when your policy requires explicitly setting the primary stage name

GET /bundles/{bundle_id}
# stage_changed = before_stage != bundle["stage"]
# optional: currentStageInfo.status is NotStarted | InProgress | Done
```

## Gotchas

- `PATCH /bundles/{id}/stages/{stageId}` only updates assignee; it does not complete a stage.
- After publish-approval-event or bundle PATCH, re-fetch and verify `bundle["stage"]` or `currentStageInfo.status` changed.
- Parallel gates need all approvals before advance.
- Reject reopens the evidence stage; it does not delete the bundle.
- Distinguish policy approval gates from Domino RBAC on the project.
