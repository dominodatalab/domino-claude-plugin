# Bundle Lifecycle

This document explains how governance bundles progress through policy stages in Domino.

Auth and `$BASE`: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200). Curl examples use `${TOKEN:+-H "Authorization: Bearer $TOKEN"}`; leave `TOKEN` unset only when step 1 (proxy) works.

## How Policies Define Stage Sequences

A policy template defines an ordered sequence of stages that a model must pass through. A typical MRM policy might use stages like:

```
Model Initiation → Development → Validation & Testing → Deployment Approval → Ongoing Monitoring → Decommission
```

Each stage has:
- **Stage ID**: A UUID (discovered via `GET /bundles/{bundleId}` → `stages[]`)
- **Name**: Human-readable label
- **Approvals**: Organizations that must sign off before the stage can advance
- **EvidenceSet**: Form-based questions to be answered (discovered via `GET /policies/{policyId}`)
- **Attachments**: Files, model versions, and reports linked to the bundle

### Stage Gating

Policies with `enforceSequentialOrder: true` require stages to be completed in order. A stage typically requires:
1. All evidence questions answered
2. Approval from the designated organization(s)

## Creating a Bundle

### Prerequisites
1. **Project ID**: Available as `DOMINO_PROJECT_ID` env var inside Domino, or from the bundle creation response
2. **Policy ID**: Discover via `GET /policy-overviews`

### Create the Bundle
```bash
curl -X POST "$BASE/bundles" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "your-project-id",
    "name": "My Model v1.0",
    "policyId": "policy-uuid"
  }'
```

The response includes:
- `id` — The bundle ID (use this for all subsequent operations)
- `policyId` — The policy UUID (used for evidence submission)
- `policyVersionId` — The policy version UUID (used for findings)
- `stages` — The full stage structure inherited from the policy
- `stageApprovals` — Approval requirements per stage with org/user IDs
- `attachments` — Evidence attached to the bundle
- `classificationValue` — Auto-populated if policy has classification rules

### One Bundle Per Model Version
Best practice: create a new bundle for each significant model version. This keeps the audit trail clean:
- `My Model v1.0` — initial model
- `My Model v1.1` — retrained with new features
- `My Model v2.0` — architecture change

## Discovering Stage IDs

After creating a bundle, inspect it to find the stage IDs:

```bash
curl -s "$BASE/bundles/$BUNDLE_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```

The response includes a `stages` array:
```json
{
    "bundleId": "...",
    "stageId": "3a32d944-...",
    "stage": {
        "id": "3a32d944-...",
        "name": "Model Initiation",
        "policyVersionId": "102f6b3b-..."
    }
}
```

**Important**: The bundle response does NOT include evidenceSet IDs. To get those, fetch the policy directly:
```bash
curl -s "$BASE/policies/$POLICY_ID" ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```

## Progressing Through Stages

Stage **status** on the bundle (`currentStageInfo.status`) is `NotStarted`, `InProgress`, or `Done`. It is derived from results and approvals, not set with `PATCH .../stages/{stageId}`.

### Assign a stage owner
`PATCH /bundles/{bundleId}/stages/{stageId}` accepts **assignee** only:
```bash
curl -X PATCH "$BASE/bundles/$BUNDLE_ID/stages/$STAGE_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -H "Content-Type: application/json" \
  -d '{"assignee": {"id": "user-uuid", "name": "username"}}'
```

### Complete a stage and move on
After evidence is submitted and approvals are recorded:

1. `POST /rpc/publish-approval-event` with the appropriate `eventType` (for example `RequestApproved`). See [APPROVAL-GATE.md](./APPROVAL-GATE.md).
2. When needed, set the primary stage name on the bundle:
```bash
curl -X PATCH "$BASE/bundles/$BUNDLE_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -H "Content-Type: application/json" \
  -d '{"stage": "Validation & Testing"}'
```

Re-fetch the bundle and confirm `stage` (name string) or `currentStageInfo.status` changed. Do not use `{"status": "Complete"}` on the stage subresource; that field is not in the API.

If the policy enforces gating and required questions are unanswered, advance steps may fail or leave the bundle non-compliant.

### Typical Stage Progression

1. **Model Initiation** — Business case, risk tier, scope, data compliance, registration
2. **Development** — MLflow logging, data docs, methodology, code reproducibility, limitations
3. **Validation & Testing** — Out-of-sample metrics, fairness, SHAP, findings, stress tests
4. **Deployment Approval** — Findings resolved, committee approval, deployment plan, access controls
5. **Ongoing Monitoring** — Performance review, drift checks, alerts, re-validation
6. **Decommission** — Replacement plan, archive, endpoint removal, stakeholder notification

## Approval Gating

Each stage has designated approver organizations. Approval typically requires a member of the organization to sign off in the Domino UI. The `stageApprovals` section of the bundle response shows:
- Which organizations need to approve each stage
- Current approval status
- Approver IDs (useful for creating findings)

## Checking Bundle Status

At any point, inspect the current state:
```bash
curl -s "$BASE/bundles/$BUNDLE_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```

Look at:
- `stage` — Current stage name
- `state` — Bundle state (e.g., "Active")
- `classificationValue` — Auto-detected risk tier
- `attachments` — What evidence has been attached (count and details)
- `stageApprovals` — Approval status per stage

## Listing All Bundles in a Project

To see all bundles:
```bash
curl -s "$BASE/bundles?projectId=$PROJECT_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```

This returns summaries of all bundles, useful for checking if a bundle already exists before creating a duplicate.
