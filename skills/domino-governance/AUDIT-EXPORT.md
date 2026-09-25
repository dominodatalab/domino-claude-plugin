# Regulatory audit export

Auditor exports one bundle: full attachment list and content, all evidence submissions and results history, all findings and comments and resolutions, all approval events, policy versions in effect at each approval, bundle report PDF, zipped.

HTTP: Governance calls use [SKILL.md Configuration](./SKILL.md#configuration). Audit trail `GET /api/audittrail/v1/...` uses the public deployment URL + Bearer (not the in-run proxy path).

## Core calls

```python
GET /bundles/{bundle_id}
# attachments = bundle["attachments"]

GET /bundles/{bundle_id}/findings

GET /results?bundleID={bundle_id}

GET /bundles/{bundle_id}/approvals

GET /api/audittrail/v1/entityHistory?entityId={bundle_id}&entityType=Bundle
# audit trail service on public deployment URL

GET /bundles/{bundle_id}/report
# application/pdf binary; write response bytes to a file, do not expect JSON base64
```

## Gotchas

- Result rows for a bundle: `GET /results?bundleID=...` (optional `policyID`, `artifactID`). Not the global audittrail.
- Attachments may be large; stream, do not load into memory.
- Policy versions in effect = policy version at each approval event timestamp, not latest.
- Export is read-only; never mutate.
