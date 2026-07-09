# Property values

Once a property is defined (see [PROPERTIES.md](./PROPERTIES.md)), you assign
**values** to individual entities here. Values are read, set, cleared, and
deleted per entity, addressed by `entityType` + `entityId`.

All examples assume the configuration block from
[SKILL.md](./SKILL.md#configuration):

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"
```

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/property-values/{entityType}/{entityId}` | GET | Get all property values for an entity |
| `/property-values/{entityType}/{entityId}` | PATCH | Set / clear values in a batch |
| `/property-values/{entityType}/{entityId}` | DELETE | Clear all values for an entity |

`entityType` must be a property-capable type:

```
dataset | project | project_template | model | app | netapp_volume | model_version | app_version
```

## Versioned entities (`?version=`)

`model_version` and `app_version` carry values per version, so they take a
`version` query parameter:

- `app_version` — `?version=` is **required**.
- `model_version` — `?version=` is **required**, *unless* `entityId` is itself
  a model-version UUID (which already encodes the version).
- All other entity types — a `version` param is **rejected**
  (`400 version is only applicable to model version and app version entities`).

## Get property values

Returns every active property permitted for the entity type, grouped by
`groupName` (ungrouped fields fall under `Miscellaneous`). Properties with no
stored value are still listed, with `value` omitted — so a UI can render the
full editable form in one call. Soft-deleted properties are never returned.

```bash
curl -s -H "$H" "$BASE/property-values/project/<project-id>" | python3 -m json.tool
```

```json
{
  "entityId": "<project-id>",
  "entityType": "project",
  "groups": [
    {
      "groupName": "Finance",
      "fields": [
        {"propertyId":"...","propertyLabel":"Budget","type":"number","status":"active","value":"50000","updatedBy":{...},"updatedAt":"..."},
        {"propertyId":"...","propertyLabel":"Review Status","type":"select","status":"active","allowedValues":[{"value":"Draft"},{"value":"Approved"}]}
      ]
    }
  ]
}
```

`select`/`multi_select` fields always include `allowedValues` so the menu can
render even when unset. `multi_select` values come back in a `values[]` array;
every other type uses the scalar `value`.

```bash
# A model version — version required (unless entityId is a version UUID)
curl -s -H "$H" "$BASE/property-values/model_version/<model-id>?version=3"

# An app version — version always required
curl -s -H "$H" "$BASE/property-values/app_version/<app-id>?version=5"
```

## Set / clear values (PATCH)

Send a batch of items. Each item targets one `propertyId`. The batch is
**best-effort**: a failing item lands in `errors[]` without aborting the rest,
which land in `applied[]`.

```bash
curl -s -X PATCH -H "$H" -H "Content-Type: application/json" \
  -d '{
        "items":[
          {"propertyId":"<budget-id>","value":"50000"},
          {"propertyId":"<review-status-id>","value":"Approved"},
          {"propertyId":"<tags-id>","values":["Oncology","Cardiology"]},
          {"propertyId":"<owner-id>","value":""}
        ]
      }' \
  "$BASE/property-values/project/<project-id>"
```

```json
{
  "entityId": "<project-id>",
  "entityType": "project",
  "applied": [
    {"propertyId":"<budget-id>","action":"set"},
    {"propertyId":"<review-status-id>","action":"set"},
    {"propertyId":"<tags-id>","action":"set"},
    {"propertyId":"<owner-id>","action":"cleared"}
  ],
  "errors": []
}
```

Rules per item:

- **`value` vs `values`** — `multi_select` properties take a `values[]` array
  and reject a scalar `value`; every other type takes `value` and rejects
  `values`.
- **Clearing** — an item with an empty `value` (and no `values`, no
  `copyPolicy`) clears any stored value. If nothing was stored, the item's
  `action` is `noop`; if a value was removed, it is `cleared`.
- **Validation** — each `value` is validated against the property's type
  (number parses as float, date is `YYYY-MM-DD`, boolean is `true`/`false`,
  url is http(s), select must be an allowed value). `multi_select` selections
  must all be allowed values; the stored order follows the property's
  `allowedValues` order and duplicates are dropped.
- **Per-item errors** — a bad item returns a message in `errors[]`, e.g.
  `value must be a valid number`, `entity type is not in the property's allowed
  entities`, or `property not found` (for an unknown or soft-deleted property).

## Copy policy (templates)

`project_template` entities can attach a **copy policy** to a value, governing
what happens to that property when a project is created from the template:

| `copyPolicy` | Behavior on instantiation |
|--------------|---------------------------|
| `copy` | Copy the template's value to the new project (default when omitted on a template) |
| `emptyRequired` | Leave empty on the new project, but require the user to fill it |
| `emptyOptional` | Leave empty on the new project, optional to fill |

```bash
curl -s -X PATCH -H "$H" -H "Content-Type: application/json" \
  -d '{"items":[
        {"propertyId":"<budget-id>","value":"0","copyPolicy":"emptyRequired"}
      ]}' \
  "$BASE/property-values/project_template/<template-id>"
```

Constraints:

- `copyPolicy` is **only** valid on template entity types
  (`400 copy policy is only valid for template entity types` otherwise).
- Must be one of `copy | emptyRequired | emptyOptional`.
- `copyPolicy:"copy"` requires a non-empty value.

## Clear all values (DELETE)

Removes every stored value for the entity (the property definitions are
untouched).

```bash
curl -s -X DELETE -H "$H" "$BASE/property-values/project/<project-id>"
# 200 → {"removedCount":4}

# Versioned:
curl -s -X DELETE -H "$H" "$BASE/property-values/app_version/<app-id>?version=5"
```

## Permissions

Property *values* use per-entity permissions, not the Librarian/Admin role that
property *definitions* require:

| Operation | Requirement |
|-----------|-------------|
| `GET` values | View access to the entity (Librarians/Admins always pass) |
| `PATCH` / `DELETE` values | Edit-property-values permission on the entity (Librarians/Admins always pass) |

A `403` on a value write means you lack edit access to that specific project /
model / app / dataset / volume, e.g.
`insufficient permissions: cannot edit property values on this project`.

## Common workflows

### Fill in a project's properties (data scientist)

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"

# 1. See what properties apply and their current values
curl -s -H "$H" "$BASE/property-values/project/$DOMINO_PROJECT_ID" | python3 -m json.tool

# 2. Set several at once
curl -s -X PATCH -H "$H" -H "Content-Type: application/json" \
  -d "{\"items\":[
        {\"propertyId\":\"<budget-id>\",\"value\":\"75000\"},
        {\"propertyId\":\"<review-status-id>\",\"value\":\"In Review\"}
      ]}" \
  "$BASE/property-values/project/$DOMINO_PROJECT_ID"
```

### Bulk-set one property across many entities (governance)

There is no batch-across-entities endpoint — loop one entity at a time,
re-fetching the token periodically for long runs.

```bash
while IFS=, read -r eid val; do
  curl -s -X PATCH -H "Authorization: Bearer $(curl -s http://localhost:8899/access-token)" \
    -H "Content-Type: application/json" \
    -d "{\"items\":[{\"propertyId\":\"<prop-id>\",\"value\":\"$val\"}]}" \
    "$BASE/property-values/project/$eid" > /dev/null && echo "set $eid=$val"
done < values.csv
```

## Documentation Reference

Confirm endpoint paths and field names against the cluster swagger before
relying on any call (see [SKILL.md](./SKILL.md#documentation-reference)):

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$DOMINO_API_HOST/api/taxonomy/swagger/doc.json"
```

- [PROPERTIES.md](./PROPERTIES.md) — defining the properties whose values you set here
- [SKILL.md](./SKILL.md) — skill overview, tags, namespaces, entity tagging
