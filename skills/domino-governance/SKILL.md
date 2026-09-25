---
name: domino-governance
description: Manage model risk governance in Domino using policies, bundles, and evidence. Covers creating governance bundles, attaching model artifacts and MLflow results as evidence, progressing through policy stages, and documenting findings. Use when the user mentions governance, compliance, bundles, policies, model risk management, SR 11-7, NIST AI RMF, or audit trails.
---

# Domino Governance Skill

This skill provides knowledge for managing model risk governance in Domino Data Lab using the Governance API.

## Configuration

Authentication: https://docs.domino.ai/cloud/reference/api/domino-api-authentication . **Do not use API keys** (`X-Domino-Api-Key`, `DOMINO_USER_API_KEY`).

Governance REST lives at `/api/governance/v1/*`. Pick the base where `GET $BASE/policy-overviews` returns **HTTP 200** (try the table rows in order):

| Context | Base | Authorization |
|---------|------|----------------|
| In-run, `DOMINO_API_PROXY` set (5.4.0+ JWT credential propagation) | `{DOMINO_API_PROXY}/api/governance/v1` | None (proxy adds starting-user JWT) |
| In-run, no proxy, governance on platform API gateway | `{DOMINO_USER_HOST or DOMINO_API_HOST}/api/governance/v1` | Bearer from `GET http://localhost:8899/access-token` |
| In-run but proxy or sidecar returns **404** on `/api/governance/v1/*` (gateway off or governance not registered on 8763) | `{public deployment URL}/api/governance/v1` | Bearer PAT or SA token |
| Outside any run | `{public deployment URL}/api/governance/v1` | Bearer PAT or SA token |

```bash
GOV="/api/governance/v1"
PREFIX="/policy-overviews"

# 1) In-run, proxy (try first when DOMINO_API_PROXY is set)
BASE="$DOMINO_API_PROXY$GOV"
curl -s "$BASE$PREFIX"

# 2) In-run, platform gateway (no proxy)
HOST="${DOMINO_USER_HOST:-$DOMINO_API_HOST}"
TOKEN="$(curl -s http://localhost:8899/access-token)"
BASE="$HOST$GOV"
curl -s "$BASE$PREFIX" -H "Authorization: Bearer $TOKEN"

# 3) Public deployment (outside run, or 404 on 1 and 2)
BASE="https://your-deployment.domino.tech$GOV"
TOKEN="$PAT_OR_SA_TOKEN"
curl -s "$BASE$PREFIX" -H "Authorization: Bearer $TOKEN"
```

Do **not** scrape the JWT `iss` claim to derive the cluster URL. Prefer `DOMINO_API_PROXY` in-run when step 1 succeeds; otherwise step 2 or 3.

**Takeaways for agents**

1. **Proxy + no header is correct only when routing works.** `DOMINO_API_PROXY` injects JWT ([product auth doc](https://docs.domino.ai/cloud/reference/api/domino-api-authentication)); it does not add `/api/governance/v1` if guardrails is not reachable on that path.
2. **Try steps 1 → 2 → 3** until `GET $BASE/policy-overviews` returns HTTP 200. Do not assume step 1 works on every deployment.
3. **In-run without proxy is not “use public URL.”** Use `DOMINO_USER_HOST` (or `DOMINO_API_HOST`) plus Bearer from `http://localhost:8899/access-token` when governance is on the platform API gateway.
4. **Public deployment URL + PAT/SA** when you are outside a run, or when step 1 or 2 returns **404** (common when the API gateway is off or governance is not registered on port 8763).
5. **Suffix is always** `/api/governance/v1` on whichever host/base you chose ([Governance API](https://docs.domino.ai/cloud/reference/api/governance-api)).

**Examples below:** Omit `Authorization` only when `TOKEN` is unset (proxy path). For gateway or public URL, set `TOKEN` and use `${TOKEN:+-H "Authorization: Bearer $TOKEN"}` in curl blocks.

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

When automating a specific flow, open the matching workflow file first instead of re-deriving from the 8-step section below.

- [BUNDLE-LIFECYCLE.md](./BUNDLE-LIFECYCLE.md) - Stage sequences, creating bundles, progressing stages
- [EVIDENCE-WORKFLOW.md](./EVIDENCE-WORKFLOW.md) - Attachment types, evidence submission, findings
- [ONBOARD-MODEL.md](./ONBOARD-MODEL.md) - Onboard a model into governance
- [EVIDENCE-ROUND-TRIP.md](./EVIDENCE-ROUND-TRIP.md) - Evidence round-trip with findings
- [APPROVAL-GATE.md](./APPROVAL-GATE.md) - Approval gate automation
- [MONITORING-REREVIEW.md](./MONITORING-REREVIEW.md) - Monitoring-driven re-review
- [RECERTIFICATION-BULK.md](./RECERTIFICATION-BULK.md) - Periodic recertification (bulk)
- [AUDIT-EXPORT.md](./AUDIT-EXPORT.md) - Regulatory audit export
- [POLICY-LIFECYCLE.md](./POLICY-LIFECYCLE.md) - Policy lifecycle and rollout
- [MODEL-RETIREMENT.md](./MODEL-RETIREMENT.md) - Model retirement
- [WAIVER-EXCEPTION.md](./WAIVER-EXCEPTION.md) - Exception or waiver
- [READ-CONTEXT.md](./READ-CONTEXT.md) - Read governance context for downstream use

## Governance API Reference

All endpoints are under `$BASE` (`/api/governance/v1`). See [Configuration](#configuration) for when to send `Authorization`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/policy-overviews` | GET | List available policy templates |
| `/bundles` | POST | Create a new governance bundle (optional inline `attachments`) |
| `/bundles/{bundleId}` | GET | Inspect bundle: stages, attachments, status |
| `/bundles/{bundleId}` | PATCH | Update bundle `state`, primary `stage` name, or `policyId` |
| `/bundles` | GET | List all bundles (filter by `projectId`) |
| `/bundles/{bundleId}/attachments` | POST | Attach evidence after create (model versions, reports) |
| `/bundles/{bundleId}/stages/{stageId}` | PATCH | Update stage **assignee** only (not stage completion) |
| `/rpc/submit-result-to-policy` | POST | Answer policy evidence questions |
| `/rpc/compute-policy` | POST | Recompute policy for a bundle (returns `ComputedPolicy`) |
| `/results/latest` | GET | Latest artifact results (`bundleID` query param) |
| `/rpc/publish-approval-event` | POST | Publish approval workflow events (approve, reject, etc.) |
| `/policies/{policyId}` | GET | Get full policy with evidenceSet IDs |
| `/findings` | POST | Create a finding (issue) during review |
| `/findings/{id}` | PUT | Update a finding (including `status`) |

## Standard 8-Step Governance Workflow

Follow these steps when setting up governance for a model:

### Step 1: Discover Policies
```bash
curl -s "$BASE/policy-overviews" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```
Review available templates. Note the `id` of the policy you want to use.

### Step 2: Get the Project ID
The project ID is needed to create a bundle. Use the `DOMINO_PROJECT_ID` environment variable (available inside Domino) or look it up via the gateway API.

### Step 3: Create a Bundle
Attachments may be inline on `POST /bundles` or added later via `POST /bundles/{id}/attachments`. Prefer inline when creating and attaching a model in one step (see [ONBOARD-MODEL.md](./ONBOARD-MODEL.md)).

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
Save the returned `id` as your `BUNDLE_ID`.

### Step 4: Inspect the Bundle
```bash
curl -s "$BASE/bundles/$BUNDLE_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```
This reveals the policy's stage structure, attachments, and approval status. **Note**: This does NOT return evidenceSet IDs — see Step 6 for how to discover those.

### Step 5: Attach Evidence
See [EVIDENCE-WORKFLOW.md](./EVIDENCE-WORKFLOW.md) for full details. Two attachment types are supported:

```bash
# Attach a registered model version
curl -X POST "$BASE/bundles/$BUNDLE_ID/attachments" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} -H "Content-Type: application/json" \
  -d '{"type":"ModelVersion","identifier":{"name":"model-name","version":5},"name":"Display Name"}'

# Attach a project file (notebook, report, etc.)
curl -X POST "$BASE/bundles/$BUNDLE_ID/attachments" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} -H "Content-Type: application/json" \
  -d '{"type":"Report","identifier":{"branch":"main","commit":"abc...","source":"git","filename":"path/to/file"},"name":"Display Name"}'
```

### Step 6: Answer Evidence Questions (EvidenceSet)

Evidence questions are the interactive forms shown in the Domino UI under each stage's "Evidence" tab. They are defined in the policy YAML as `evidenceSet` items.

#### 6a. Discover EvidenceSet IDs

EvidenceSet IDs are NOT in the bundle response. Fetch them from the **policy** endpoint:

```bash
curl -s "$BASE/policies/$POLICY_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
```

The response contains `stages[]` → `evidenceSet[]` → `artifacts[]` with full UUIDs for each evidence item and artifact.

#### 6b. Submit Answers

```bash
curl -X POST "$BASE/rpc/submit-result-to-policy" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
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
Stage completion is driven by evidence, approvals, and workflow events, not by `status: Complete` on the stage subresource. `PATCH /bundles/{bundleId}/stages/{stageId}` only updates **assignee**. After evidence and approvals:

1. Publish approval events (see [APPROVAL-GATE.md](./APPROVAL-GATE.md)):
```bash
curl -X POST "$BASE/rpc/publish-approval-event" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "bundle-uuid",
    "policyId": "policy-uuid",
    "projectId": "project-uuid",
    "eventType": "RequestApproved",
    "approvalId": "approval-uuid"
  }'
```

2. When the policy requires explicitly setting the primary stage name, use `PATCH /bundles/{bundleId}`:
```bash
curl -X PATCH "$BASE/bundles/$BUNDLE_ID" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -H "Content-Type: application/json" \
  -d '{"stage": "Next stage name from policy"}'
```

Re-fetch the bundle and verify `stage` (primary stage name) or `currentStageInfo.status` (`NotStarted`, `InProgress`, `Done`) changed before continuing. Details: [BUNDLE-LIFECYCLE.md](./BUNDLE-LIFECYCLE.md).

### Step 8: Document Findings (if any)
```bash
curl -X POST "$BASE/findings" \
  ${TOKEN:+-H "Authorization: Bearer $TOKEN"} -H "Content-Type: application/json" \
  -d '{
    "bundleId": "bundle-uuid",
    "policyVersionId": "policy-version-uuid",
    "name": "Finding title",
    "description": "Detailed description...",
    "severity": "High",
    "approver": {"id": "org-uuid", "name": "model-gov-org"},
    "assignee": {"id": "user-uuid", "name": "username"}
  }'
```
Close or resolve with **PUT** `/findings/{id}` and `"status": "Done"` (not `PATCH` or `state: Closed`). See [EVIDENCE-ROUND-TRIP.md](./EVIDENCE-ROUND-TRIP.md).
Get the `policyVersionId` and user/org IDs from the bundle response (Step 4).

## Viewing in Domino UI

After creating a bundle and attaching evidence, the bundle is visible in the Domino UI:
**Project** > **Govern** > **Bundles** > click the bundle name

The UI shows:
- **Overview** — Stage progression and classification
- **Evidence** tab (per stage) — Interactive forms for evidenceSet questions
- **Attachments** tab — Files, model versions, and reports
- **Findings** tab — Documented issues with severity

## After compute-policy (polling)

`POST /rpc/compute-policy` returns **200** with a `ComputedPolicy` body. Freshness lives on artifact results, not a single top-level flag.

1. Call `POST /rpc/compute-policy` with `bundleId` and `policyId`.
2. Poll `GET /results/latest?bundleID={bundleId}` (and optional `policyID`, `artifactID`) until the artifacts you care about have `isLatest: true`, or inspect `results[].isLatest` on the compute response when present.
3. Only then treat evidence as current for submit, stage advance, or read-context output.

Reuse this loop in every workflow that calls `compute-policy` (see [ONBOARD-MODEL.md](./ONBOARD-MODEL.md), [EVIDENCE-ROUND-TRIP.md](./EVIDENCE-ROUND-TRIP.md), [READ-CONTEXT.md](./READ-CONTEXT.md)).

## Known platform behaviors

Short pointers; full gotchas live in the workflow files linked under [Related Documentation](#related-documentation).

| Behavior | Where |
|----------|--------|
| Governance base URL (proxy vs gateway vs public on 404) | [Configuration](#configuration) |
| Verify stage actually advanced after approvals | [APPROVAL-GATE.md](./APPROVAL-GATE.md), [BUNDLE-LIFECYCLE.md](./BUNDLE-LIFECYCLE.md) |
| Poll after `compute-policy` | [After compute-policy (polling)](#after-compute-policy-polling) |
| `ModelVersion` attachment `identifier.name` | [EVIDENCE-WORKFLOW.md](./EVIDENCE-WORKFLOW.md), [ONBOARD-MODEL.md](./ONBOARD-MODEL.md) |
| Draft vs submitted evidence (`isLatest`) | [EVIDENCE-WORKFLOW.md](./EVIDENCE-WORKFLOW.md) |
| Close findings (PUT + `status`, new evidence first) | [EVIDENCE-ROUND-TRIP.md](./EVIDENCE-ROUND-TRIP.md) |
| Policy version retire / upgrade on bundles | [POLICY-LIFECYCLE.md](./POLICY-LIFECYCLE.md) |
| Multi-bundle per model | [READ-CONTEXT.md](./READ-CONTEXT.md) |
| Policy attach RPC vs nucleus guardrails proxy | [POLICY-LIFECYCLE.md](./POLICY-LIFECYCLE.md) |
| Open findings before stage advance | [EVIDENCE-ROUND-TRIP.md](./EVIDENCE-ROUND-TRIP.md) |

## Documentation Reference

Before writing or verifying any API call, use the cluster swagger to confirm current endpoint paths and field names. Use public docs for workflow context and field explanations.

**Governance API base:** See [Configuration](#configuration) (proxy, in-run gateway + access-token, or public URL + PAT/SA when governance 404s on the sidecar). Do not scrape the JWT `iss` claim.

Fetch the governance swagger spec (requires bearer token against the public deployment URL):
```bash
curl -H "Authorization: Bearer $TOKEN" "https://your-deployment.domino.tech/api/governance/swagger/doc.json"
# Browser UI (must be logged in): https://your-deployment.domino.tech/api/governance/swagger/index.html
```

**Public docs (workflow context and field explanations):**
- Governance overview: https://docs.domino.ai/cloud/platform-capabilities/features/governance
- API reference: https://docs.domino.ai/cloud/reference/api/domino-open-api (Governance tags)

For governance workflows and pitfalls, see [Related Documentation](#related-documentation).
