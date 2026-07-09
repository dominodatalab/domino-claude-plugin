---
name: tags-and-properties
description: Manage Domino tags and properties via the Taxonomy API. Covers tags/namespaces (create, list, update, delete; tag entities — project, model, dataset, app, project_template, netapp_volume; query by tag; autocomplete; merge; CSV import/export) AND properties (typed metadata fields — text, number, date, boolean, url, user, organization, select, multi_select — with per-entity values, groups, and versioned entities like model_version/app_version). Use when organizing entities with tags, building hierarchical namespaces, defining typed metadata fields, setting property values on projects/models/apps, finding entities by tag, bulk-tagging during onboarding, or migrating taxonomy across environments.
---

# Domino Tags and Properties Skill

## Description

This skill covers Domino's Taxonomy API, which manages two complementary
metadata systems for organizing entities (projects, models, datasets, apps,
project templates, NetApp volumes):

- **Tags** — hierarchical labels grouped into namespaces. An entity either has
  a tag or it doesn't.
- **Properties** — typed metadata *fields* (`text`, `number`, `date`,
  `select`, …), each holding a value per entity.

It documents every public endpoint with curl examples that work today against
a Domino cluster where the taxonomy service is enabled. Properties are covered
in depth in [PROPERTIES.md](./PROPERTIES.md) (definitions) and
[PROPERTY-VALUES.md](./PROPERTY-VALUES.md) (per-entity values).

## Activation

Activate this skill when the user wants to:

- Tag a project, model, dataset, app, project template, or NetApp volume
- Find all entities that share a tag, or query by multiple tags
- Build a hierarchical taxonomy (namespaces with nested tags)
- Bulk-tag entities during onboarding
- Migrate a taxonomy tree across Domino environments (CSV export/import)
- Merge duplicate tags
- Tune autocomplete results in a tagging UI
- Define typed metadata fields (properties) — e.g. a `Budget` number, a
  `Review Date`, an `Owner` user, or a `Status` single-select
- Set, read, or clear property values on an entity (incl. versioned entities
  like `model_version` / `app_version`)
- Group properties or manage property definitions across a deployment

## Configuration

Auth via the local access-token endpoint per the
[Skill Authoring Standards](../../CONTRIBUTING.md#skill-authoring-standards).
Never use `DOMINO_USER_API_KEY`.

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
# Taxonomy is served through the Domino API host gateway.
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Namespace** | Top-level group for **tags** (e.g. `Indication`, `Analysis`). Has `label`, optional `description`, and `allowMultipleAssignments` flag. |
| **Tag** | A label inside a namespace. Can be hierarchical via `parentId` (e.g. `Clinical_Data / SDTM`). Has `label`, `namespaceId`, optional `description` and `parentId`, and `status` (`active` / `inactive`). |
| **Property** | A typed metadata *field* — has a `label`, a `type` (`text`, `number`, `date`, `boolean`, `url`, `user`, `organization`, `user_or_org`, `select`, `multi_select`), a set of `allowedEntities`, an optional `groupName`, and (for select types) `allowedValues`. See [PROPERTIES.md](./PROPERTIES.md). |
| **Property value** | The typed value a property holds for one specific entity, set via `PATCH /property-values`. See [PROPERTY-VALUES.md](./PROPERTY-VALUES.md). |
| **Property group** | Free-form `groupName` string that buckets properties in the values view; ungrouped properties fall under `Miscellaneous`. |
| **EntityType** | Enum over entities. Tags apply to `dataset`, `project`, `project_template`, `model`, `app`, `netapp_volume`. Properties additionally support the *versioned* types `model_version` and `app_version`. |
| **`allowMultipleAssignments`** | (Tags) When `true`, an entity can hold multiple tags from the same namespace. When `false`, applying a new tag from the namespace replaces any existing one. |
| **Taxonomy tree** | The full nested view: namespaces → root tags → child tags. Returned by `GET /taxonomy`. |
| **Limits** | `GET /config` returns `maxDepth` (max tag nesting), `maxLabelLength` (max characters per label), `maxSelectAllowedValuesCount` (max options on a select property), and `maxSelectAllowedValueLength` (max length of one option). |

## Taxonomy API Reference

All endpoints are under `$BASE` (`/api/taxonomy/v1`). Authenticate every
request with `Authorization: Bearer $TOKEN`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/config` | GET | Get configuration limits |
| `/taxonomy` | GET | Get full taxonomy tree (nested namespaces + tags) |
| `/namespaces` | GET / POST | List / create namespaces |
| `/namespaces/{namespaceId}` | GET / PUT / DELETE | Get / update / delete a namespace |
| `/namespaces/bulk-delete` | POST | Bulk delete namespaces — see [BULK-OPS.md](./BULK-OPS.md) |
| `/tags` | GET / POST | List / create tags |
| `/tags/{tagId}` | GET / PUT / DELETE | Get / update / delete a tag |
| `/tags/{tagId}/entities` | GET | List entities tagged with a tag |
| `/tags/autocomplete` | GET | Autocomplete tag suggestions for a query |
| `/tags/bulk-delete` | POST | Bulk delete tags — see [BULK-OPS.md](./BULK-OPS.md) |
| `/rpc/merge-tags` | POST | Merge tags — see [BULK-OPS.md](./BULK-OPS.md) |
| `/entities` | GET | Get entities by one or more tag IDs |
| `/entity-tags` | GET / DELETE | Get tags for entities / delete all tags for an entity |
| `/rpc/tag-entity` | POST | Tag an entity |
| `/rpc/untag-entity` | POST | Remove specific tags from an entity |
| `/rpc/export-to-file` | POST | Export taxonomy as CSV — see [IMPORT-EXPORT.md](./IMPORT-EXPORT.md) |
| `/rpc/import-from-file` | POST | Import taxonomy from CSV — see [IMPORT-EXPORT.md](./IMPORT-EXPORT.md) |
| `/rpc/validate-file` | POST | Validate a CSV before import — see [IMPORT-EXPORT.md](./IMPORT-EXPORT.md) |
| `/properties` | GET / POST | List / create property definitions — see [PROPERTIES.md](./PROPERTIES.md) |
| `/properties/{propertyId}` | GET / PUT / DELETE | Get / update / soft-delete a property — see [PROPERTIES.md](./PROPERTIES.md) |
| `/property-groups` | GET | List distinct property group names — see [PROPERTIES.md](./PROPERTIES.md) |
| `/property-values/{entityType}/{entityId}` | GET / PATCH / DELETE | Get / set-clear / delete-all property values for an entity — see [PROPERTY-VALUES.md](./PROPERTY-VALUES.md) |

## Common Workflows

### Workflow 1 — Tag a project (data scientist)

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"

# 1. Discover the tag you want to apply
curl -s -H "$H" "$BASE/tags/autocomplete?q=clinical" | python3 -m json.tool

# 2. Apply it to your project
curl -X POST -H "$H" -H "Content-Type: application/json" \
  -d "{\"entityType\":\"project\",\"entityId\":\"$DOMINO_PROJECT_ID\",\"tagIds\":[\"<tag-id>\"]}" \
  "$BASE/rpc/tag-entity"

# 3. Verify
curl -s -H "$H" "$BASE/entity-tags?entityType=project&entityIds=$DOMINO_PROJECT_ID"
```

### Workflow 2 — Build a hierarchical taxonomy (governance admin)

```bash
# Create a namespace
NS=$(curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"label":"Analysis","description":"Type of analysis","allowMultipleAssignments":false}' \
  "$BASE/namespaces" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Create a parent tag
PARENT=$(curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d "{\"label\":\"Interim\",\"namespaceId\":\"$NS\"}" \
  "$BASE/tags" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Create a child tag under it
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d "{\"label\":\"Milestone_01\",\"namespaceId\":\"$NS\",\"parentId\":\"$PARENT\"}" \
  "$BASE/tags"
```

Tag depth is capped at `maxDepth` from `GET /config` (5 on most deployments).

### Workflow 3 — Find all entities with a tag (discovery)

```bash
# Single tag
curl -s -H "$H" "$BASE/tags/<tag-id>/entities" | python3 -m json.tool

# Multiple tags (intersection) — tagIds is a REPEATED query parameter, not comma-separated
curl -s -H "$H" "$BASE/entities?tagIds=<tag-id-1>&tagIds=<tag-id-2>&entityType=project"
```

Both endpoints return paginated results with `meta.pagination.{total,limit,offset}`.
Paginate with `?limit=50&offset=50`.

> **Heads-up:** `tagIds` on `/entities` must be repeated per value
> (`?tagIds=A&tagIds=B`). Comma-separating returns
> `400 {"message":"invalid tag ID: A,B"}`. By contrast, `entityIds` on
> `/entity-tags` *is* comma-separated. Yes, the convention is inconsistent.

### Workflow 4 — Autocomplete in a tagging UI (discovery)

```bash
curl -s -H "$H" "$BASE/tags/autocomplete?q=clin"
```

Response:

```json
{"items":[
  {"id":"23ca6d78-...","path":"Clinical_Data"},
  {"id":"0b55bf67-...","path":"Clinical_Data / SDTM"},
  {"id":"57454f72-...","path":"Clinical_Data / ADaM"}
]}
```

`path` shows the full hierarchy with ` / ` between levels — surface it
verbatim in the UI to disambiguate same-named tags in different branches.

## Namespaces

```bash
# List
curl -s -H "$H" "$BASE/namespaces?limit=50&offset=0"

# Create (label required)
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"label":"Indication","description":"Therapeutic area","allowMultipleAssignments":true}' \
  "$BASE/namespaces"
# 201 → returns full Namespace including id, status, timestamps

# Get one
curl -s -H "$H" "$BASE/namespaces/<id>"

# Update (label and status both required)
curl -s -X PUT -H "$H" -H "Content-Type: application/json" \
  -d '{"label":"Indication","description":"updated","status":"active","allowMultipleAssignments":true}' \
  "$BASE/namespaces/<id>"

# Delete — cascades through the namespace's tags and entity-tag bindings.
# Returns 204 even on a non-empty namespace. There is no "are you sure" prompt.
# Reach for `namespaces/bulk-delete` when removing several at once.
curl -s -X DELETE -H "$H" "$BASE/namespaces/<id>"
# 204 No Content
```

## Tags

```bash
# List with optional filters
curl -s -H "$H" "$BASE/tags?namespaceId=<ns>&limit=50"

# Create (label and namespaceId required, parentId optional for hierarchy)
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"label":"SDTM","namespaceId":"<ns>","description":"Study Data Tabulation Model","parentId":"<parent-tag>"}' \
  "$BASE/tags"

# Get one — includes entityCount broken down by EntityType
curl -s -H "$H" "$BASE/tags/<id>"

# Update (label required; you can change parentId to re-parent within the same namespace)
curl -s -X PUT -H "$H" -H "Content-Type: application/json" \
  -d '{"label":"SDTMv2","description":"new desc","status":"active","parentId":"<new-parent>"}' \
  "$BASE/tags/<id>"

# Delete (single)
curl -s -X DELETE -H "$H" "$BASE/tags/<id>"
# 204 No Content
```

## Entity Tags

```bash
# Tag an entity (entityType, entityId, tagIds[] all required)
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"entityType":"project","entityId":"<project-id>","tagIds":["<tag-1>","<tag-2>"]}' \
  "$BASE/rpc/tag-entity"
# 201 → {"entityId":"...","entityType":"project","entityName":"...","tags":[...]}
#
# Constraint: if `tagIds` contains more than one tag from the SAME namespace,
# that namespace must have `allowMultipleAssignments=true`. Otherwise:
# 400 → {"message":"namespace does not allow multiple tag assignments per entity"}
# To replace a tag in a single-assign namespace, send a separate request — the
# new tag overwrites the prior one for that namespace.

# Remove specific tags from an entity
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"entityType":"project","entityId":"<project-id>","tagIds":["<tag-1>"]}' \
  "$BASE/rpc/untag-entity"
# 200 → {"entityId":"...","entityType":"project","entityName":"...","removedTagIds":[...]}

# Get tags for one or more entities (entityIds is comma-separated)
curl -s -H "$H" "$BASE/entity-tags?entityType=project&entityIds=<id-1>,<id-2>"
# 200 → {"data":{"<id-1>":[Tag,...], "<id-2>":[Tag,...]}}

# Remove ALL tags from an entity
curl -s -X DELETE -H "$H" "$BASE/entity-tags?entityType=project&entityId=<id>"
# 200 → {"removedCount":N}
```

`entityType` must be one of: `dataset`, `project`, `project_template`,
`model`, `app`, `netapp_volume`. Other values return 400.

## Taxonomy Tree

```bash
curl -s -H "$H" "$BASE/taxonomy" | python3 -m json.tool
```

Returns an array of `TreeNamespace` objects, each with nested `tags` of type
`TreeTag`:

```json
[{
  "id":"821e1455-...",
  "label":"Indication",
  "description":"Therapeutic area",
  "status":"active",
  "allowMultipleAssignments":false,
  "tags":[
    {"id":"...", "label":"Oncology", "status":"active", "children":[
      {"id":"...", "label":"Breast_Cancer", "status":"active", "children":[]}
    ]}
  ]
}]
```

Use this to render the full taxonomy in a UI in one call.

## Config

```bash
curl -s -H "$H" "$BASE/config"
# {"maxDepth":5,"maxLabelLength":128,"maxSelectAllowedValuesCount":100,"maxSelectAllowedValueLength":2048}
```

| Field | Applies to |
|-------|-----------|
| `maxDepth` | Max tag nesting depth |
| `maxLabelLength` | Max characters for a namespace/tag/property label (and property group name) |
| `maxSelectAllowedValuesCount` | Max options on a `select`/`multi_select` property |
| `maxSelectAllowedValueLength` | Max length of a single select option |

Surface these limits in any UI that lets users create tags, namespaces, or
properties so the user gets immediate validation feedback.

## Properties

Properties are typed metadata *fields* — a complement to tags. Where a tag is
present-or-absent, a property holds a typed value per entity (`Budget = 50000`,
`Review Date = 2026-01-31`, `Status = "Approved"`).

Two layers:

1. **Definitions** — the field schema (`label`, `type`, `allowedEntities`,
   optional `groupName` and `allowedValues`). Managed under `/properties`;
   create/update/delete requires the Librarian or Admin role. Full reference:
   [PROPERTIES.md](./PROPERTIES.md).
2. **Values** — the value a property holds for a specific entity. Managed under
   `/property-values/{entityType}/{entityId}`; permissions are per-entity, not
   role-based. Full reference: [PROPERTY-VALUES.md](./PROPERTY-VALUES.md).

### Workflow 5 — Define a property (governance admin)

```bash
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{
        "label":"Review Status",
        "groupName":"Governance",
        "type":"select",
        "allowedEntities":["project","model"],
        "allowedValues":[{"value":"Draft"},{"value":"In Review"},{"value":"Approved"}]
      }' \
  "$BASE/properties"
# 201 → full Property with id, status, timestamps
```

`type` is immutable after creation. `select`/`multi_select` require
`allowedValues`; other types reject it. `project_template` is not allowed in
`allowedEntities` — use `project` and it applies to templates too. See
[PROPERTIES.md](./PROPERTIES.md).

### Workflow 6 — Set property values on an entity (data scientist)

```bash
# See which properties apply and their current values
curl -s -H "$H" "$BASE/property-values/project/$DOMINO_PROJECT_ID" | python3 -m json.tool

# Set several at once (best-effort batch: per-item failures don't abort)
curl -s -X PATCH -H "$H" -H "Content-Type: application/json" \
  -d '{"items":[
        {"propertyId":"<budget-id>","value":"50000"},
        {"propertyId":"<review-status-id>","value":"Approved"}
      ]}' \
  "$BASE/property-values/project/$DOMINO_PROJECT_ID"
```

`multi_select` properties take a `values[]` array; all other types use `value`.
An empty `value` clears the property. Versioned entities (`model_version`,
`app_version`) require a `?version=` query param. See
[PROPERTY-VALUES.md](./PROPERTY-VALUES.md).

## Bulk Operations and Tag Merging

See [BULK-OPS.md](./BULK-OPS.md) for `tags/bulk-delete`,
`namespaces/bulk-delete`, and `rpc/merge-tags`.

## Import / Export

See [IMPORT-EXPORT.md](./IMPORT-EXPORT.md) for `rpc/export-to-file`,
`rpc/import-from-file`, and `rpc/validate-file` — useful for migrating a
taxonomy across Domino environments.

## Best Practices

- **One namespace per dimension.** Don't pile orthogonal concepts (e.g.
  Indication and Analysis Type) into one namespace; separate so users can
  filter cleanly.
- **Use `allowMultipleAssignments=false`** for mutually exclusive concepts
  (e.g. "Phase" — a project is in exactly one phase). Use `true` when an
  entity can plausibly carry several values from the same namespace
  (e.g. multiple "Indication" tags).
- **Hierarchy via `parentId`** rather than encoding hierarchy into labels
  (e.g. `Clinical_Data/SDTM`). This lets autocomplete and tree views render
  the structure for you.
- **Query `GET /config` once** at app startup and cache `maxLabelLength` /
  `maxDepth` for client-side validation.
- **Pin tag IDs, not labels.** Tag labels can be renamed via `PUT /tags/{id}`;
  IDs are stable. Workflows that automate tagging should reference tag IDs.
- **Discoverability**: use `GET /taxonomy` for full-tree views,
  `GET /tags/autocomplete?q=...` for typeaheads, and
  `GET /entities?tagIds=A&tagIds=B&entityType=...` (one `tagIds` per value,
  not comma-separated) for filtered lists.

## Troubleshooting

### `Public api endpoint not found` (404)

The taxonomy service is not registered on the gateway you are calling. Two
common causes:

1. **Wrong base URL.** Taxonomy is served through the Domino API host gateway.
   Ensure `BASE` is set to `$DOMINO_API_HOST/api/taxonomy/v1` and that
   `$DOMINO_API_HOST` is populated (it is set automatically in Domino
   workspaces, jobs, and apps).
2. **Taxonomy not enabled on this deployment.** Older or stripped-down
   deployments may not include the taxonomy microservice. Confirm with
   your Domino administrator before working around this.

### `400 Bad Request` on `POST /rpc/tag-entity`

Ensure `entityType` is exactly one of:
`dataset | project | project_template | model | app | netapp_volume`.
Casing matters — `Project` and `PROJECT` will be rejected.

### `400` on `POST /tags`

`namespaceId` must reference an existing namespace, and the `label` must be
non-empty and ≤ `maxLabelLength` (from `/config`). If you intend to nest the
tag, `parentId` must reference a tag in the same namespace.

### Deleting a namespace removes its tags too

`DELETE /namespaces/{id}` is a cascading delete: it removes the namespace,
every tag inside it, and every entity-tag binding pointing at those tags.
There is no "namespace must be empty" check — confirm with the user before
calling it against a shared cluster. `namespaces/bulk-delete` has the same
cascade behavior across multiple IDs.

## Documentation Reference

Before writing or verifying any API call, use the cluster swagger to confirm current endpoint paths and field names. Use public docs for workflow context and field explanations.

**Taxonomy API base:** `$DOMINO_API_HOST/api/taxonomy/v1` (served through the
Domino API host gateway; `$DOMINO_API_HOST` is populated automatically in
workspaces, jobs, and apps).

Fetch the taxonomy swagger spec (requires bearer token):
```bash
TOKEN=$(curl -s http://localhost:8899/access-token)

curl -H "Authorization: Bearer $TOKEN" "$DOMINO_API_HOST/api/taxonomy/swagger/doc.json"

# Browser UI — use the external cluster URL (must be logged in):
# https://<your-cluster>/api/taxonomy/swagger/index.html
```

**Public docs (workflow context and field explanations):**
- [Taxonomy API guide](https://docs.dominodatalab.com/en/cloud/api_guide/fc6b7c/taxonomy-api/)
- [Skill Authoring Standards](../../CONTRIBUTING.md#skill-authoring-standards)
- [PROPERTIES.md](./PROPERTIES.md) — property definitions (typed metadata fields)
- [PROPERTY-VALUES.md](./PROPERTY-VALUES.md) — setting property values on entities
- [BULK-OPS.md](./BULK-OPS.md) — bulk-delete + merge-tags + migration patterns
- [IMPORT-EXPORT.md](./IMPORT-EXPORT.md) — CSV export/import for taxonomy migration
