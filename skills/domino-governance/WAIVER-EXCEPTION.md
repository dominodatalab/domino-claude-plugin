# Exception or waiver

Submitter and approver request a deviation on a bundle, document justification, get approver sign-off, track expiry via finding due date, write an audit entry, bundle proceeds despite missing evidence.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
POST /findings {
    "bundleId": bundle_id,
    "policyVersionId": policy_version_id,
    "name": "Waiver: <short title>",
    "description": justification,
    "severity": "Medium",
    "approver": {...},
    "assignee": {...},
    "dueDate": expiry_iso8601,
}
```

## Gotchas

- Waiver is modeled as a finding with `dueDate` for expiry, not a separate API or `expiresAt` field.
- Create requires approver, assignee, bundleId, name, policyVersionId, severity.
- Expiring waivers need a re-review trigger (monitor or scheduled).
