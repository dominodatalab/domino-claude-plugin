# Bundle Lifecycle

This document explains how governance bundles progress through policy stages in Domino.

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
  -H "X-Domino-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "your-project-id",
    "name": "My Model v1.0",
    "description": "Description of the model being governed",
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
  -H "X-Domino-Api-Key: $API_KEY"
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
curl -s "$BASE/policies/$POLICY_ID" -H "X-Domino-Api-Key: $API_KEY"
```

## Progressing Through Stages

### Starting a Stage
When you begin work on a stage:
```bash
curl -X PATCH "$BASE/bundles/$BUNDLE_ID/stages/$STAGE_ID" \
  -H "X-Domino-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress"}'
```

### Completing a Stage
After all evidence is attached and questions answered:
```bash
curl -X PATCH "$BASE/bundles/$BUNDLE_ID/stages/$STAGE_ID" \
  -H "X-Domino-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "Complete"}'
```

If the policy enforces gating and required questions are unanswered, this may fail.

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
  -H "X-Domino-Api-Key: $API_KEY"
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
  -H "X-Domino-Api-Key: $API_KEY"
```

This returns summaries of all bundles, useful for checking if a bundle already exists before creating a duplicate.
