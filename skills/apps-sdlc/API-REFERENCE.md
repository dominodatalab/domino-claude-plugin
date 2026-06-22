# Apps v1 API Reference (SDLC)

Base path: `/api/apps/v1`. All calls require `Authorization: Bearer $TOKEN`.
Source of truth: `apps/public/apps-v1-public-api.yaml` in the `domino` repo.

> Instance **read** endpoints (list instances, logs, realTimeLogs, views, instance DELETE)
> were **not** migrated to v1 — they remain under `/api/apps/beta` (kept active + deprecated
> for backward compatibility). Everything below is v1.

Common error responses for write endpoints: `400` bad request, `401` unauthorized,
`403` forbidden, `404` not found, `422` unprocessable entity, `500` server error.

## App endpoints

### `GET /apps` — listAppsV1
List Apps with filtering/pagination. **Published Apps only by default.**

Key query params: `projectId`, `name`, `ownerId`, `publisherId`, `status`, `tagIds[]`
(AND semantics), `entryPoint` (exact match — useful to find publish-into-existing targets),
`includeTemplateApps` (default false), `sortField` (`name|lastUpdated|status|views|lastViewed`,
default `lastViewed`), `sortOrder` (`asc|desc`), `limit`, `offset`.

- **`draftsOnly`** (boolean, default false) — when `true`, returns **only draft** Apps;
  otherwise only published Apps. (Drafts are still author-scoped regardless.)

Response: `ListAppsResponseV1 { items: [AppSummaryResponseV1], metadata: PaginatedMetadataV1 }`.

### `POST /apps` — createAppV1
Create a **published** App with an initial version. Does **not** start an instance.

Request `AppCreationRequestV1`:
- `name` (string, **required**)
- `projectId` (string, **required**)
- `visibility` (string, **required**) — `AUTHENTICATED | GRANT_BASED | GRANT_BASED_STRICT | PUBLIC`
- `description`, `entryPoint` (immutable after creation), `renderIFrame`, `discoverable`,
  `mountDatasets` (all optional)
- `accessStatuses` ([AppAccessStatus], optional)
- `configurationType` (`STANDARD` default | `AISYSTEM`)
- `initialVersion` (AppVersionCreationRequestV1, optional)
- `sendNotifications` (boolean, default false)

Response: `AppResponseV1`.

### `GET /apps/{appId}` — getAppV1
Response: `AppResponseV1`.

### `PATCH /apps/{appId}` — updateAppV1
Update App metadata/defaults only (never versions/instances; `entryPoint` not accepted).

Request `AppUpdateRequestV1` (all optional): `name`, `description`, `visibility`,
`accessStatuses`, `discoverable`, `mountDatasets` (takes effect on next version creation),
`sendNotifications`. Response: `AppResponseV1`.

### `DELETE /apps/{appId}` — deleteAppV1
Empty 200 response.

### `POST /apps/drafts` — createAppDraftV1
**Idempotent per workspace.** Ensures a draft App exists for the caller's workspace: creates a
new draft on first call, or returns the existing draft (applying any supplied `app` fields as a
PATCH) on re-entry. Always returns 200.

Request `CreateAppDraftRequestV1`:
- `workspaceId` (string, **required**) — must be visible to the caller
- `app` (DraftAppFields, optional) — `name`, `description`, `visibility`, `accessStatuses`,
  `discoverable`, `renderIFrame`, `mountDatasets`, `configurationType`
- `initialVersion` (CreateAndStartAppVersionRequestV1, optional) — when present, a
  create-and-start runs after the draft is ensured; `entryScript` is **required** when supplied
- `targetAppId` (string, optional) — advisory hint for a later publish-into-existing

Response `CreateAppDraftResponseV1`:
- `app` (AppResponseV1) — always present
- `version` (AppVersionResponseV1) — only when `initialVersion` supplied
- `instance` (AppInstanceSummaryResponseV1) — only when `initialVersion` supplied **and** start succeeded
- `warnings` ([string]) — non-fatal (e.g. start failed to initiate)

### `POST /apps/{appId}/publish` — publishAppV1
Publish a draft's content into a new or existing published App. `{appId}` is the **draft** id.

Request `PublishAppRequestV1`:
- `targetAppId` (string, optional) — present → publish-into-existing; absent → publish-as-new
- `appOverrides` (AppOverridesV1, optional) — **publish-as-new only**: `name`, `description`,
  `vanityUrl` (in `apps` namespace; random if omitted), `visibility`, `accessStatuses`,
  `discoverable`, `renderIFrame`, `mountDatasets`
- `versionOverrides` (VersionOverridesV1, optional) — overrides on a copy of the draft's
  last-run version: `content` (AppVersionContentUpdate), `deployment` (AppVersionDeploymentUpdate),
  `bundleId`, `tags`, `description` (release notes)
- `start` (boolean, default false) — start the result's newest version after publish
- `startOverrides` (StartAppVersionRequestV1, optional) — deployment-only overrides for that start
- `sendNotifications` (boolean, default false) — publish-as-new only

Response `PublishAppResponseV1`: `app` (destination), `version` (newly inserted),
`instance` (only if `start=true` and succeeded), `warnings`.

Validation: publish-into-existing requires draft `entryScript` == target `entryPoint` and matching
`configurationType` (else **422**). Draft never previewed + missing content → `NoPreviewedVersionError`.

## AppVersion endpoints

### `GET /apps/{appId}/versions` — listAppVersionsV1
Response: `ListAppVersionsResponseV1 { items: [AppVersionResponseV1], metadata }`.

### `POST /apps/{appId}/versions` — createAppVersionV1
Create a new version. Does **not** start an instance.

Request `AppVersionCreationRequestV1`: `content` (AppVersionContentUpdate), `deployment`
(AppVersionDeploymentUpdate), `bundleId`, `tags`, `description`, `workspaceId` (draft only).
Response: `AppVersionResponseV1`.

### `POST /apps/{appId}/versions/createAndStart` — createAndStartAppVersionV1
Create a version **and** launch it in one request. The version is always persisted; if start
fails, the response carries the version plus `warnings`. Any currently-running version of the
same App is **stopped first**. For **drafts**, omitted content reference fields default to the
previous running version's values (so you can change just one thing).

Request `CreateAndStartAppVersionRequestV1`: `content`, `deployment`, `bundleId` (n/a on drafts),
`tags`, `description`, `startOverrides` (StartAppVersionRequestV1).

Response (**201**) `AppVersionCreateAndStartResponseV1`: `version` (always), `instance` (only if
start succeeded), `warnings`.

### `GET /apps/{appId}/versions/{versionId}` — getAppVersionV1
Response: `AppVersionResponseV1`.

### `PATCH /apps/{appId}/versions/{versionId}` — updateAppVersionV1
**Metadata only.** Accepts `description`, `tags`, `bundleId` (settable **once**; existence
validated), `workspaceId` (draft only). Sending content/deployment fields → **422**.
Response: `AppVersionResponseV1`.

### `POST /apps/{appId}/versions/{versionId}/start` — startAppVersionV1
Launch an instance for a version. Optional `deployment` overrides (`hardwareTierId`,
`autoscalingSpecification`, `vanityUrl`, `renderIFrame`) are mirrored back onto the version so it
always reflects the last launch. `renderIFrame` is rejected (422) on draft starts.

Request `StartAppVersionRequestV1 { deployment: AppVersionDeploymentUpdate }`.
Response: `AppVersionResponseV1`.

### `POST /apps/{appId}/versions/{versionId}/stop` — stopAppVersionV1
Stop the running instance for this version. Empty 200 response.

### `POST /apps/{appId}/versions/{versionId}/liveSync` — liveSyncAppVersion
Push changed code into the **active preview instance** of a draft version. The caller supplies
current commit IDs; the server syncs only what changed since the last sync.

Request `LiveSyncRequest` (all optional/nullable): `mainRepoCommitId`, `dfsCommitId`,
`importedRepoCommits` ([`{ repoId, ref }`]).

Response `LiveSyncResponse { triggered: boolean }` — `false` if everything was already up to date.
**404** if no active preview instance exists.

## Core schemas

### AppResponseV1
Required: `id`, `name`, `project` (AppProjectResponse), `entryPoint`, `renderIFrame`, `url`,
`views`, `configurationType`, `authorship` (AppAuthorship), `accessControl` (AppAccessControl),
`mountDatasets`.
Optional: `description`, `vanityUrl`, `currentVersion` (AppVersionResponseV1), `updatedAt`,
`thumbnailEtag`, `taxonomyTags`, `properties`.

- **AppAuthorship**: `isDraft` (boolean, **required** — true only for drafts), `author` (nullable).
- **AppAccessControl**: `visibility`, `accessStatuses` ([{userId, status: ALLOWED|DENIED|PENDING}]), `discoverable`.

### AppVersionResponseV1
Required: `id`, `createdAt`, `updatedAt`, `tags`.
Optional: `versionNumber`, `description`, `currentInstance` (AppInstanceSummaryResponseV1),
`bundle` (AppVersionBundle), `content` (AppVersionContent), `deployment` (AppVersionDeployment).

- **AppVersionContent** (content/reproducibility): `mountDatasets` (required), `dfsCommitId`,
  `gitRef` (GitRef), `resolvedCommits`, `importedGitRepoRefs` ([ImportedGitRepoRef], sorted by
  repoId), `environmentId`, `environmentRevisionId`, `dataPlaneId` (nullable),
  `externalVolumeMountIds`, `netAppVolumeIds`, `entryScript`,
  `extendedIdentityPropagationToAppsEnabled`.
- **AppVersionDeployment** (execution): `hardwareTierId`, `autoscalingSpecification`
  (AppAutoscalingSpecification), `vanityUrl`.
- **GitRef**: `type` (`head|commitId|branches|tags|custom`, required), `value` (optional).
- **ImportedGitRepoRef**: `repoId`, `repoName`, `gitRef`.

### AppInstanceSummaryResponseV1
Required: `id`, `createdAt`, `status`.
Optional: `describeUrl`, `dfsCommitId`, `gitCommitId`, `publisher` (nullable),
`lastSynced` (AppInstanceLastSyncedState, **preview only**).

- **AppInstanceLastSyncedState**: `syncedAt` (required), `mainRepoCommitId` (nullable),
  `dfsCommitId` (nullable), `importedRepoCommits`.

### Update (request) schemas
- **AppVersionContentUpdate** (all optional; omitted → App default or previous draft value):
  `dfsCommitId`, `gitRef`, `resolvedCommits`, `importedGitRepoRefPatches`
  ([`{ repoId, gitRef? }`] — null `gitRef` drops the repo), `environmentId`,
  `environmentRevisionId`, `dataPlaneId` (auto-derived from `hardwareTierId` if omitted),
  `externalVolumeMountIds`, `netAppVolumeIds`, `mountDatasets`, `entryScript`,
  `extendedIdentityPropagationToAppsEnabled`.
- **AppVersionDeploymentUpdate** (all optional): `hardwareTierId`, `autoscalingSpecification`,
  `vanityUrl`, `renderIFrame` (published starts only — 422 on draft starts).

### AppAutoscalingSpecification
`enabled` (required); optional `useSessionAffinity`, `minReplicas` (1–30), `maxReplicas` (1–30),
`targetCpuAvgUtilizationPct` (1–100), `targetMemoryAvgUtilizationPct` (1–100),
`scaleDownStabilizationWindowSeconds` (0–3600), `scaleUpStabilizationWindowSeconds` (0–3600).
> Not usable for preview instances — previews cannot autoscale.

### AppConfigurationType
`STANDARD` (default) | `AISYSTEM`.
