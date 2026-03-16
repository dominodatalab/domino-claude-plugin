---
name: domino-governance
description: Manage model risk governance in Domino using policies, bundles, and evidence. Covers creating governance bundles, attaching model artifacts and MLflow results as evidence, progressing through policy stages, and documenting findings. Use when the user mentions governance, compliance, bundles, policies, model risk management, SR 11-7, NIST AI RMF, or audit trails.
---

# Domino Governance Skill

This skill provides knowledge for managing model risk governance in Domino Data Lab using the Governance API.

## Configuration

```bash
API_KEY="$DOMINO_USER_API_KEY"
BASE="${DOMINO_GOVERNANCE_HOST:-$DOMINO_API_HOST}/api/governance/v1"
```

Some deployments expose governance on a different host than the internal API. If so, set `DOMINO_GOVERNANCE_HOST` to override the base URL. Check `domino_project_settings.md` for project-specific overrides.

## Key Concepts

### Policy (Template)
A **policy** is a reusable governance template that defines the stages, evidence requirements, and approval gates a model must pass through. Examples: SR 11-7, NIST AI RMF, internal model risk frameworks. Policies are created by administrators in the Domino UI.

### Bundle (Living Document)
A **bundle** is the compliance document for a *specific model* in a *specific project*. It follows a policy and accumulates evidence as the model progresses through development, validation, and approval. One project can have multiple bundles (e.g., one per model version).

### Evidence (Proof)
Evidence comes in two forms:
1. **Attachments** — Files, model versions, and reports attached to the bundle (visible in the "Attachments" tab)
2. **EvidenceSet answers** — Responses to policy-defined form questions (visible in the "Evidence" tab for each stage)

### Finding (Issue)
A **finding** documents a problem, risk, or concern discovered during review. Findings have severity levels and are tracked as part of the audit trail.

## Related Documentation

- [BUNDLE-LIFECYCLE.md](./BUNDLE-LIFECYCLE.md) - Stage sequences, creating bundles, progressing stages
- [EVIDENCE-WORKFLOW.md](./EVIDENCE-WORKFLOW.md) - Attachment types, evidence submission, findings

## Governance API Reference

All endpoints are under `$BASE` (`/api/governance/v1`). Authenticate with `X-Domino-Api-Key: $API_KEY`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/policy-overviews` | GET | List available policy templates |
| `/bundles` | POST | Create a new governance bundle |
| `/bundles/{bundleId}` | GET | Inspect bundle: stages, attachments, status |
| `/bundles` | GET | List all bundles (filter by `projectId`) |
| `/bundles/{bundleId}/attachments` | POST | Attach evidence (model versions, reports) |
| `/rpc/submit-result-to-policy` | POST | Answer policy evidence questions |
| `/bundles/{bundleId}/stages/{stageId}` | PATCH | Update stage status (In Progress, Complete) |
| `/policies/{policyId}` | GET | Get full policy with evidenceSet IDs |
| `/findings` | POST | Create a finding (issue) during review |

## Standard 8-Step Governance Workflow

Follow these steps when setting up governance for a model:

### Step 1: Discover Policies
```bash
curl -s "$BASE/policy-overviews" \
  -H "X-Domino-Api-Key: $API_KEY"
```
Review available templates. Note the `id` of the policy you want to use.

### Step 2: Get the Project ID
The project ID is needed to create a bundle. Use the `DOMINO_PROJECT_ID` environment variable (available inside Domino) or look it up via the gateway API.

### Step 3: Create a Bundle
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
Save the returned `id` as your `BUNDLE_ID`.

### Step 4: Inspect the Bundle
```bash
curl -s "$BASE/bundles/$BUNDLE_ID" \
  -H "X-Domino-Api-Key: $API_KEY"
```
This reveals the policy's stage structure, attachments, and approval status. **Note**: This does NOT return evidenceSet IDs — see Step 6 for how to discover those.

### Step 5: Attach Evidence
See [EVIDENCE-WORKFLOW.md](./EVIDENCE-WORKFLOW.md) for full details. Two attachment types are supported:

```bash
# Attach a registered model version
curl -X POST "$BASE/bundles/$BUNDLE_ID/attachments" \
  -H "X-Domino-Api-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"type":"ModelVersion","identifier":{"name":"model-name","version":5},"name":"Display Name"}'

# Attach a project file (notebook, report, etc.)
curl -X POST "$BASE/bundles/$BUNDLE_ID/attachments" \
  -H "X-Domino-Api-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"type":"Report","identifier":{"branch":"main","commit":"abc...","source":"git","filename":"path/to/file"},"name":"Display Name"}'
```

### Step 6: Answer Evidence Questions (EvidenceSet)

Evidence questions are the interactive forms shown in the Domino UI under each stage's "Evidence" tab. They are defined in the policy YAML as `evidenceSet` items.

#### 6a. Discover EvidenceSet IDs

EvidenceSet IDs are NOT in the bundle response. Fetch them from the **policy** endpoint:

```bash
curl -s "$BASE/policies/$POLICY_ID" \
  -H "X-Domino-Api-Key: $API_KEY"
```

The response contains `stages[]` → `evidenceSet[]` → `artifacts[]` with full UUIDs for each evidence item and artifact.

#### 6b. Submit Answers

```bash
curl -X POST "$BASE/rpc/submit-result-to-policy" \
  -H "X-Domino-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "bundle-uuid",
    "policyId": "policy-uuid",
    "evidenceId": "evidence-uuid",
    "content": {
      "artifact-uuid": "value"
    }
  }'
```

**Key details**:
- Use `policyId` (NOT `policyVersionId`)
- `evidenceId` is the evidence set item UUID (from policy response)
- `content` is a map of `{artifactId: value}`
- For **radio/textinput/textarea/select**: value is a string
- For **checkbox/multiSelect**: value is an array of strings
- Submit one artifact at a time per call, or multiple artifacts in the same evidence item together

### Step 7: Progress Stages
As evidence is collected and approvals obtained:
```bash
curl -X PATCH "$BASE/bundles/$BUNDLE_ID/stages/$STAGE_ID" \
  -H "X-Domino-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "Complete"}'
```

### Step 8: Document Findings (if any)
```bash
curl -X POST "$BASE/findings" \
  -H "X-Domino-Api-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{
    "bundleId": "bundle-uuid",
    "policyVersionId": "policy-version-uuid",
    "name": "Finding title",
    "title": "Finding title",
    "description": "Detailed description...",
    "severity": "High",
    "approver": {"id": "org-uuid", "name": "model-gov-org"},
    "assignee": {"id": "user-uuid", "name": "username"}
  }'
```
Get the `policyVersionId` and user/org IDs from the bundle response (Step 4).

## Viewing in Domino UI

After creating a bundle and attaching evidence, the bundle is visible in the Domino UI:
**Project** > **Govern** > **Bundles** > click the bundle name

The UI shows:
- **Overview** — Stage progression and classification
- **Evidence** tab (per stage) — Interactive forms for evidenceSet questions
- **Attachments** tab — Files, model versions, and reports
- **Findings** tab — Documented issues with severity
