---
name: domino-taxonomy
description: Manage Domino taxonomies — namespaces, tags, and entity tagging — via the Taxonomy API. Covers creating, listing, updating, and deleting tags and namespaces; tagging entities (project, model, dataset, app, project_template, netapp_volume); querying entities by tag; tag autocomplete; merging tags; and importing/exporting taxonomy trees as CSV. Use when organizing projects with tags, building hierarchical namespaces, finding all entities with a given tag, bulk-tagging during onboarding, or migrating taxonomy across environments.
---

# Domino Taxonomy Skill

## Description

This skill covers Domino's Taxonomy API for organizing entities (projects,
models, datasets, apps, project templates, NetApp volumes) under hierarchical
tags grouped into namespaces. It documents every public endpoint with curl
examples that work today against a Domino cluster where the taxonomy service
is enabled.

## Activation

Activate this skill when the user wants to:

- Tag a project, model, dataset, app, project template, or NetApp volume
- Find all entities that share a tag, or query by multiple tags
- Build a hierarchical taxonomy (namespaces with nested tags)
- Bulk-tag entities during onboarding
- Migrate a taxonomy tree across Domino environments (CSV export/import)
- Merge duplicate tags
- Tune autocomplete results in a tagging UI

## Configuration

Auth via the local access-token endpoint per the
[Skill Authoring Standards](../../CONTRIBUTING.md#skill-authoring-standards).
Never use `DOMINO_USER_API_KEY`.

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"
```

If your cluster's internal gateway (`$DOMINO_API_HOST`) does not expose
taxonomy and you receive `Public api endpoint not found`, see
[Troubleshooting](#troubleshooting).

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Namespace** | Top-level group (e.g. `Indication`, `Analysis`). Has `label`, optional `description`, and `allowMultipleAssignments` flag. |
| **Tag** | A label inside a namespace. Can be hierarchical via `parentId` (e.g. `Clinical_Data / SDTM`). Has `label`, `namespaceId`, optional `description` and `parentId`, and `status` (`active` / `inactive`). |
| **EntityType** | Enum over taggable entities: `dataset`, `project`, `project_template`, `model`, `app`, `netapp_volume`. |
| **`allowMultipleAssignments`** | When `true`, an entity can hold multiple tags from the same namespace. When `false`, applying a new tag from the namespace replaces any existing one. |
| **Taxonomy tree** | The full nested view: namespaces → root tags → child tags. Returned by `GET /taxonomy`. |
| **Limits** | `GET /config` returns `maxDepth` (max tag nesting) and `maxLabelLength` (max characters per label). |

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

# Multiple tags (intersection)
curl -s -H "$H" "$BASE/entities?tagIds=<tag-id-1>,<tag-id-2>&entityType=project"
```

Both endpoints return paginated results with `meta.pagination.{total,limit,offset}`.
Paginate with `?limit=50&offset=50`.

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

# Delete (only if empty — namespaces with tags cannot be deleted directly)
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
# {"maxDepth":5,"maxLabelLength":128}
```

Surface these limits in any UI that lets users create tags or namespaces so
the user gets immediate validation feedback.

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
  `GET /entities?tagIds=...&entityType=...` for filtered lists.

## Troubleshooting

### `Public api endpoint not found` (404)

The taxonomy service is not registered on the gateway you are calling. Two
common causes:

1. **Internal vs public gateway.** On some clusters, `$DOMINO_API_HOST`
   points at an internal gateway (e.g. `nucleus-frontend.domino-platform`)
   that does not expose the taxonomy service. Try the public hostname of
   your Domino deployment (the one in your browser address bar) instead.
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

### Cannot delete a namespace

`DELETE /namespaces/{id}` requires the namespace to be empty. Either delete
its tags first (single or via `tags/bulk-delete`) or use
`namespaces/bulk-delete` which handles cascades.

## Documentation Reference

- [Taxonomy API guide](https://docs.dominodatalab.com/en/cloud/api_guide/fc6b7c/taxonomy-api/)
- [Skill Authoring Standards](../../CONTRIBUTING.md#skill-authoring-standards)
- [BULK-OPS.md](./BULK-OPS.md) — bulk-delete + merge-tags + migration patterns
- [IMPORT-EXPORT.md](./IMPORT-EXPORT.md) — CSV export/import for taxonomy migration
