---
name: domino-apps-sdlc
description: Iteratively develop, preview, and publish Domino Apps using the App Development Life Cycle (Draft → Preview → Publish). Covers creating a draft App from a workspace, starting preview instances, live-syncing code changes, and publishing to a new or existing published App via the Apps v1 API. Use when the user mentions app drafts, app preview, publishing an app, iterative app development, the Apps SDLC, "draft/preview/publish", or the EnableAppsSDLC feature flag.
---

# Domino Apps SDLC (Draft / Preview / Publish)

This skill covers the **App Development Life Cycle** in Domino Data Lab — the
draft → preview → publish model for Domino Apps — accessed through the **Apps v1 API**
(`/api/apps/v1`), gated by the `EnableAppsSDLC` feature flag.

> **Related:** This skill covers the *platform lifecycle* of an App (draft/preview/publish, the
> v1 API). For *building and configuring the app itself* — `app.sh`, ports, base-path, React/Vite
> frameworks, proxy routing, CI/CD — see the **`domino-app-deployment`** skill.

> **Who uses the API (and who doesn't).** Humans iterating on an app do it in the **workspace
> UI** — the inner loop (create draft, preview, live-sync code) is driven by the UI/executor,
> not by people running curl. The API is for **automation and agent-assisted tasks**:
> - **CI/CD & MLOps** — publish on merge, programmatic versioning, scripted teardown.
>   The endpoints that make sense here: `POST /apps` (direct create), `POST /apps/{id}/publish`,
>   `GET /apps`, version listing, `stop`.
> - **Agent-assisted** — when Claude acts on a user's behalf ("publish my app", "stop these
>   previews") it drives the API because it can't click the UI.
>
> The draft/preview/`liveSync` inner-loop endpoints are documented below for completeness and
> automation, but treat them as **UI/internal-facing** — see the caveat on `liveSync`.

> **Version / flag:** `EnableAppsSDLC` — default **on** since 6.3.0. If the API returns
> 404/403 for the draft or publish endpoints, the flag is likely disabled on that cluster.

## Configuration

```bash
# Inside a Domino workspace/job, an access token is served locally:
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/apps/v1"   # e.g. https://<cluster>/api/apps/v1
# Authenticate every call with:  -H "Authorization: Bearer $TOKEN"
```

The `projectId` and `workspaceId` you need are available in-workspace as
`$DOMINO_PROJECT_ID` and the workspace's own id.

## Key Concepts

### Draft App vs Published App
A **Draft App** and a **Published App** are two **separate** App records (separate
`model_products` documents), distinguished by the App-level boolean `isDraft`
(surfaced in responses as `authorship.isDraft`). There is **no** `status` field on a
version — draft-ness is a property of the App, not the version.

- A **draft App** is workspace-scoped, **visible only to its author**, has no vanity URL
  (it uses the `app-drafts` namespace and is addressed by id), and **cannot autoscale**
  its preview. It does not appear in app lists, discovery, or search for anyone but the author.
- A **published App** is the normal, shareable App: it has a vanity URL, honors visibility
  /access grants, appears in listings, and can autoscale.

A draft is created **lazily on the first preview** from a workspace and linked 1:1 to that
workspace. Stopping the workspace stops the preview; deleting the workspace deletes the draft.

### App, AppVersion, AppInstance
- **App** — the top-level record (draft or published). Owns metadata, visibility, vanity URL.
- **AppVersion** — an immutable snapshot of *content/reproducibility* (git ref, DFS commit,
  environment, entry script, volumes, datasets). One App has many versions.
- **AppInstance** — a running deployment of a version. A preview instance has
  `isPreview = true` and reports `lastSynced` state. Previews cannot autoscale.

### Preview instance
A preview is just an AppInstance launched from a **draft** version. `isPreview` is derived
from `App.isDraft` at start time. Previews support **live sync** (push code changes into the
running instance without a restart); published instances do not.

### The configuration-vs-deployment field split
Editing a version's fields behaves differently depending on the field category:

| Category | Fields | Effect of changing |
| --- | --- | --- |
| **Content / reproducibility** | git ref, DFS commit, resolved commits, imported git repo refs, environment + revision, external volume mounts, NetApp volume mounts, entry script, `mountDatasets` | Requires a **new AppVersion** (old instance stopped) |
| **Deployment / execution** | hardware tier, autoscaling spec, vanity URL, render-iframe | **In-place** update + instance **restart**, no new version |
| **Metadata** | `description`, `tags` | In place, **no restart, no new version** |
| **Immutable** | `entryPoint` (App-level), `bundleId` (set once) | Cannot be changed after creation |

This split is enforced server-side: sending content/deployment fields to
`PATCH .../versions/{versionId}` returns **422** — that endpoint only accepts metadata.

## Two ways to get a Published App

Both are gated by `EnableAppsSDLC`.

1. **Direct create** — `POST /api/apps/v1/apps` (`createAppV1`). Creates a **published**
   App immediately with an initial version (a version is always created), but does **not**
   start an instance. Use this when you already know the final config and don't need to iterate.

   > Spec note: the v1 OpenAPI `description` for this endpoint currently reads "Create an App
   > in draft state" — that wording is stale. The code creates a published App (`isDraft = false`).
   > Drafts are created via `POST /apps/drafts`, never via `POST /apps`.

2. **Draft → Preview → Publish** — the iterative workflow from a workspace:
   - `POST /api/apps/v1/apps/drafts` (`createAppDraftV1`) — ensure a draft exists for the
     workspace (idempotent). Pass `initialVersion` to create a version **and** start a preview
     in one round-trip.
   - `POST /api/apps/v1/apps/{appId}/versions/createAndStart` — add a new version and (re)start
     the preview as you iterate.
   - `POST /api/apps/v1/apps/{appId}/versions/{versionId}/liveSync` — push code changes into the
     running preview without a full restart. **Caveat:** this is an inner-loop call invoked by the
     workspace UI/executor (the caller has to supply current commit SHAs); it is not intended for
     a human or agent to drive by hand. Documented here for completeness.
   - `POST /api/apps/v1/apps/{appId}/publish` (`publishAppV1`) — promote the draft to a
     published App.

See **[DRAFT-LIFECYCLE.md](./DRAFT-LIFECYCLE.md)** for the full end-to-end walkthrough and
**[API-REFERENCE.md](./API-REFERENCE.md)** for every endpoint's request/response schema.

## Publish semantics

**"Publishing" just means producing non-draft content.** There is no separate publish state — an
App or AppVersion is published exactly when `isDraft = false`. So directly creating non-draft
content **is** publishing, and the `/publish` endpoint is simply the variant that *sources* that
content from an existing draft:

| Operation | Equivalent direct create |
| --- | --- |
| `publish` as-new (from a draft) | `POST /apps` (`createAppV1`) — creates a non-draft App + version |
| `publish` into-existing (from a draft) | `POST /apps/{appId}/versions` on a published App — adds a non-draft AppVersion |

In other words, `POST /apps` and `POST /apps/{appId}/versions` (on a published App) are the
"publish without a draft" paths; `POST /apps/{appId}/publish` is the "publish what I previewed in
a draft" path. All three land non-draft content.

`POST /api/apps/v1/apps/{appId}/publish` has two modes, selected by `targetAppId`:

- **Publish-as-new** (no `targetAppId`): creates a brand-new published App (new id, vanity URL
  in the `apps` namespace, `isDraft = false`) from the draft's last-run version. App-level
  fields come from `appOverrides`; version fields from `versionOverrides`. Equivalent to a direct
  `createAppV1`, but seeded from the draft.
- **Publish-into-existing** (`targetAppId` set): adds a new AppVersion to an existing published
  App. The server **validates** that the draft's `entryScript` matches the target App's
  `entryPoint` and that the `configurationType` matches — mismatches return **422**. Equivalent to
  a direct `createAppVersionV1` on that App, but seeded from the draft.

Publish is **non-destructive**: the draft and its preview instance persist afterward. If the
draft was never previewed (no "last-run version" to copy), required content must be supplied via
`versionOverrides`, otherwise publish fails (`NoPreviewedVersionError`).

## Auth model (preview access)

Preview instances do **not** use a separate auth endpoint. nginx is handed the **same**
consumer access URL as production Apps — `GET /v4/modelProducts/consumer/{appId}/access` — and
the authorizer runs a `draftAuthorGuard` first: for a draft, access is allowed **only** if the
requesting principal is the draft's author (internal/super-user principals bypass, so workspace
stop/delete cleanup can cascade). So a preview is reachable only by its author, by reusing the
normal access path — not by a role check or a dedicated `/drafts/access` route.

## Troubleshooting

| Symptom | Cause / resolution |
| --- | --- |
| Draft App not visible to teammates / not in app list | **Expected.** Drafts are author-only and excluded from listings, discovery, and search. |
| Preview won't autoscale | **Expected.** Preview instances cannot autoscale; only published App instances can. |
| `422` on `PATCH .../versions/{versionId}` | That endpoint accepts **metadata only** (`description`, `tags`, `bundleId`). Content/deployment changes need a new version (`createAndStart`) or a `start` with deployment overrides. |
| `422` on publish-into-existing | `entryScript` ≠ target App's `entryPoint`, or `configurationType` mismatch. Publish-as-new or pick a matching target. |
| `NoPreviewedVersionError` on publish | Draft was never previewed; supply required content via `versionOverrides`. |
| `renderIFrame` rejected (422) on a draft start | `renderIFrame` is only valid when starting a **published** App's version. |
| 404 on draft/publish endpoints | `EnableAppsSDLC` likely disabled on the cluster. |
| `liveSync` returns `triggered: false` | No-op — all supplied commits already match the running preview's last-synced state. |
| `liveSync` returns 404 | No active preview instance for that version. Start one first. |

## Verification / docs

The Apps v1 contract lives in the repo at `apps/public/apps-v1-public-api.yaml`. Confirm
endpoint paths and field names against the running cluster's swagger before relying on them, and
regenerate specs with `dev/bazel/update_api_specs.sh` after backend changes.

> **Unconfirmed detail:** the exact served preview ingress prefix (`/preview/<id>` vs
> `/app-drafts/preview/<id>`) is produced by `generateModelProductUri` in the external
> `domino-common` jar and is not verifiable from the `domino` repo alone. Verify against a
> live cluster before documenting a literal preview URL.
