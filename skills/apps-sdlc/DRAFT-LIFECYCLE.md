# Draft → Preview → Publish: end-to-end walkthrough

The iterative App Development Life Cycle, driven from a workspace. All calls use
`BASE=$DOMINO_API_HOST/api/apps/v1` and `-H "Authorization: Bearer $TOKEN"`
(see [SKILL.md](./SKILL.md) for setup). Gated by `EnableAppsSDLC`.

## The shape of the flow

```
workspace ──(1) create draft + first preview──▶ Draft App ──(2) iterate: createAndStart / liveSync──▶ Preview instance
                                                     │
                                                     └──(3) publish ──▶ Published App (new, or new version on existing)
```

The draft is created **lazily** and tied to the workspace 1:1. Stopping the workspace stops the
preview; deleting the workspace deletes the draft. The draft is **author-only** throughout.

## 1. Create the draft and start the first preview

`POST /apps/drafts` is idempotent per workspace — call it freely; it returns the existing draft if
one already exists. Supply `initialVersion` to create a version and start a preview in one call.

```bash
curl -s -X POST "$BASE/apps/drafts" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "workspaceId": "'"$WORKSPACE_ID"'",
    "app": { "name": "Sales Dashboard (draft)", "visibility": "GRANT_BASED" },
    "initialVersion": {
      "content": {
        "entryScript": "app.sh",
        "gitRef": { "type": "head" },
        "environmentId": "'"$ENV_ID"'",
        "mountDatasets": true
      },
      "deployment": { "hardwareTierId": "'"$HW_TIER_ID"'" }
    }
  }'
```

Response (`CreateAppDraftResponseV1`) gives you `app.id` (the draft App id),
`version.id`, and `instance.id` (the preview). Note `app.authorship.isDraft == true`.
If `warnings` is non-empty, the draft/version exist but the preview start had a non-fatal issue.

> `entryScript` is **required** inside `initialVersion`. Content fields you omit fall back to
> App-level defaults.

## 2. Iterate

### Change content (new version) — `createAndStart`
Any change to a content/reproducibility field (git ref, DFS commit, environment, entry script,
volumes, datasets) needs a **new version**. `createAndStart` makes the version and relaunches the
preview, stopping the previous one first. For a draft, fields you omit inherit the previous
running version's values — so change just what you need:

```bash
curl -s -X POST "$BASE/apps/$DRAFT_APP_ID/versions/createAndStart" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{ "content": { "environmentId": "'"$NEW_ENV_ID"'" } }'
```

Returns **201** with `version` (always persisted) and `instance` (if start succeeded).

### Push code changes without a restart — `liveSync`
> **This is an inner-loop call the workspace UI/executor makes, not something a human or agent
> drives by hand** — the caller has to supply the current commit SHAs from the workspace. Shown
> here for completeness and automation; in normal use the UI handles it on code change.

If you've only changed code (new commits) and want them reflected in the **running** preview
without a relaunch, live-sync it. Supply the current commit IDs; the server syncs only deltas:

```bash
curl -s -X POST "$BASE/apps/$DRAFT_APP_ID/versions/$VERSION_ID/liveSync" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{ "mainRepoCommitId": "'"$SHA"'", "dfsCommitId": "'"$DFS_SHA"'" }'
```

`{ "triggered": true }` = sync dispatched; `{ "triggered": false }` = already up to date.
**404** = no active preview instance (start one first).

### Change deployment settings (no new version)
Hardware tier / autoscaling changes restart the **same** version in place — use `start` with
deployment overrides (note: previews **cannot autoscale**, and `renderIFrame` is rejected on
draft starts):

```bash
curl -s -X POST "$BASE/apps/$DRAFT_APP_ID/versions/$VERSION_ID/start" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{ "deployment": { "hardwareTierId": "'"$BIGGER_TIER"'" } }'
```

### Stop / inspect
- Stop the preview: `POST /apps/{appId}/versions/{versionId}/stop`.
- Read version + current instance: `GET /apps/{appId}/versions/{versionId}` (`currentInstance.status`,
  `currentInstance.lastSynced`).
- Instance **logs/views** are still on the `beta` API (not migrated to v1).

## 3. Publish

`POST /apps/{appId}/publish` where `{appId}` is the **draft** id. It copies the draft's
**last-run** version. Publish is **non-destructive** — the draft and its preview survive.

### Publish as a new App (no `targetAppId`)

```bash
curl -s -X POST "$BASE/apps/$DRAFT_APP_ID/publish" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "appOverrides": { "name": "Sales Dashboard", "vanityUrl": "sales-dashboard", "visibility": "GRANT_BASED" },
    "versionOverrides": { "description": "Initial release" },
    "start": true
  }'
```

Creates a new published App (new id, vanity URL in the `apps` namespace, `isDraft = false`) with
the first version. `start: true` launches it. Response carries `app`, `version`, and `instance`.

### Publish into an existing App (`targetAppId` set)

```bash
curl -s -X POST "$BASE/apps/$DRAFT_APP_ID/publish" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{ "targetAppId": "'"$EXISTING_APP_ID"'", "versionOverrides": { "description": "v2 — perf fixes" }, "start": true }'
```

Adds a new version to the target App. The server **validates** the draft's `entryScript` equals
the target App's `entryPoint` and that `configurationType` matches — a mismatch returns **422**.
To find candidate targets, list published apps filtered by `entryPoint`:
`GET /apps?entryPoint=app.sh`.

### Publishing without ever previewing
If the draft was never previewed, there's no last-run version to copy — supply the required
content via `versionOverrides.content`, or publish fails with `NoPreviewedVersionError`.

## Cleanup
The draft is bound to the workspace: **stop** the workspace → preview stops; **delete** the
workspace → draft is deleted. There's no separate "delete draft" step in the normal flow.
