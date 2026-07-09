# Property definitions

Properties are **typed metadata fields** you attach to Domino entities — a
project can carry a `Budget` number, a `Review Date`, an `Owner` user, and a
`Status` single-select, all independent of its tags. This file covers the
property *definitions* (the schema). For assigning values to entities see
[PROPERTY-VALUES.md](./PROPERTY-VALUES.md).

All examples assume the configuration block from
[SKILL.md](./SKILL.md#configuration):

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"
```

## Tags vs. properties

| | Tag | Property |
|---|---|---|
| Shape | A label, optionally nested under a namespace | A typed field (`text`, `number`, `select`, …) |
| Value | Presence/absence — an entity either has the tag or not | A typed value per entity (`42`, `2026-01-31`, `"Oncology"`) |
| Grouping | Namespace | `groupName` (free-form string) |
| Entity scope | `allowedEntities` is implicit (any taggable type) | `allowedEntities` is declared per property |
| Managed by | `/tags`, `/namespaces` | `/properties`, `/property-values` |

## Property types

Set `type` at creation — it is **immutable** afterward (`PUT` cannot change it;
to change type, delete and recreate).

| Type | Value format | Notes |
|------|--------------|-------|
| `text` | any string (≤ 1000 chars) | |
| `number` | parseable float (`"42"`, `"3.14"`, `"-1e3"`) | |
| `date` | ISO-8601 date `YYYY-MM-DD` | |
| `boolean` | `"true"` or `"false"` | |
| `url` | http(s) URL with a host | |
| `user` | a user identifier string | no format check beyond non-empty |
| `organization` | an org identifier string | no format check beyond non-empty |
| `user_or_org` | a user or org identifier string | no format check beyond non-empty |
| `select` | one of `allowedValues` | single choice |
| `multi_select` | subset of `allowedValues` | value carried in a `values[]` array |

`select` and `multi_select` **require** a non-empty `allowedValues` list; all
other types **reject** `allowedValues`.

## Allowed entities

`allowedEntities` declares which entity types a property applies to. Valid
values:

```
dataset | project | model | app | netapp_volume | model_version | app_version
```

- At least one is required.
- `project_template` is **rejected** in `allowedEntities` (400
  `invalid entity type`). Templates inherit the `project` schema — define the
  property with `project` in `allowedEntities` and it applies to project
  templates automatically. See [PROPERTY-VALUES.md](./PROPERTY-VALUES.md#copy-policy-templates)
  for the template copy-policy behavior.

## Labels, groups, and limits

- **Label** — required. Allowed characters: letters, digits, spaces, hyphens,
  underscores (`^[a-zA-Z0-9 _-]+$`). Trimmed; max length = `maxLabelLength`
  from `GET /config` (128 default). Labels are unique — a duplicate returns
  `409 property with this label already exists`.
- **groupName** — optional, same character/length rules as the label. A blank
  or whitespace-only group collapses to "no group"; ungrouped properties are
  bucketed under `Miscellaneous` in the values view.
- **allowedValues** (select types) — each item is `{"value": "...",
  "subfield": "..."}` (`subfield` optional). Stored verbatim in submission
  order. Limits from `GET /config`: at most `maxSelectAllowedValuesCount`
  (100 default) options, each ≤ `maxSelectAllowedValueLength` (2048 default).

## Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/properties` | POST | Create a property | Librarian / Admin |
| `/properties` | GET | List properties | any authenticated user |
| `/properties/{propertyId}` | GET | Get one property | any authenticated user |
| `/properties/{propertyId}` | PUT | Update a property | Librarian / Admin |
| `/properties/{propertyId}` | DELETE | Soft-delete a property | Librarian / Admin |
| `/property-groups` | GET | List distinct group names | any authenticated user |

## Create a property

Label, `type`, and at least one `allowedEntities` are required.

```bash
# A simple number property on projects
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{
        "label":"Budget",
        "groupName":"Finance",
        "description":"Approved budget in USD",
        "type":"number",
        "allowedEntities":["project"]
      }' \
  "$BASE/properties"
# 201 → full Property incl. id, status:"active", createdBy, timestamps
```

```bash
# A single-select property with options
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{
        "label":"Review Status",
        "type":"select",
        "allowedEntities":["project","model"],
        "allowedValues":[{"value":"Draft"},{"value":"In Review"},{"value":"Approved"}]
      }' \
  "$BASE/properties"
```

## Get / list

```bash
# Get one — includes allowedValues, allowedEntities, status, audit fields
curl -s -H "$H" "$BASE/properties/<id>" | python3 -m json.tool

# List with filters, sorting, pagination
curl -s -H "$H" "$BASE/properties?entityType=project&search=budget&sort=label&order=asc&limit=50&offset=0"
```

`GET /properties` query params:

| Param | Values | Default |
|-------|--------|---------|
| `entityType` | filters to properties whose `allowedEntities` contains this type | — |
| `search` | matches label or description | — |
| `sort` | `label`, `groupName`, `createdAt` | `label` |
| `order` | `asc`, `desc` | `asc` |
| `limit` | page size | 50 |
| `offset` | page offset | 0 |

Response is `{"data":[PropertyListItem,...],"meta":{"pagination":{total,limit,offset},"search","filters","sort"}}`.

## Update a property

`label` and `allowedEntities` are required in the body. `type` is **not** a
field — it cannot change. You may add or remove `allowedValues` options;
removing an in-use option is allowed (stored values are not retroactively
re-validated).

```bash
curl -s -X PUT -H "$H" -H "Content-Type: application/json" \
  -d '{
        "label":"Budget (USD)",
        "groupName":"Finance",
        "description":"Approved annual budget",
        "allowedEntities":["project","app"],
        "allowedValues":[]
      }' \
  "$BASE/properties/<id>"
# 200 → updated Property
```

## Delete a property

Deletion is a **soft delete**: the property's status flips to `deleted`, it
stops appearing in lists and value views, but existing stored values are
retained (so a later recreate/undelete workflow can recover them). There is no
cascade prompt.

```bash
curl -s -X DELETE -H "$H" "$BASE/properties/<id>"
# 204 No Content
```

## List property groups

Returns the distinct, non-empty `groupName` values across active properties —
useful for rendering a grouped property editor.

```bash
curl -s -H "$H" "$BASE/property-groups"
# 200 → {"groups":["Finance","Governance"]}
```

This lists only real group names. The `Miscellaneous` bucket that ungrouped
properties fall under in the values view (see
[PROPERTY-VALUES.md](./PROPERTY-VALUES.md#get-property-values)) is synthetic and
is **not** returned here.

## Troubleshooting

### `403 insufficient permissions: requires Librarian or Admin role`

Creating, updating, and deleting property *definitions* requires the Librarian,
SysAdmin, or CloudAdmin role. Reading definitions and setting *values* do not —
see [PROPERTY-VALUES.md](./PROPERTY-VALUES.md#permissions).

### `400 invalid entity type` on create/update

Every entry in `allowedEntities` must be one of
`dataset | project | model | app | netapp_volume | model_version | app_version`.
`project_template` is rejected here — use `project` and it applies to templates
too.

### `400 allowed values are only valid for select and multi_select properties`

You sent `allowedValues` on a non-select type. Omit it. Conversely,
`select`/`multi_select` require at least one allowed value
(`400 at least one allowed value is required...`).

### `409 property with this label already exists`

Labels are unique. Pick a different label or update the existing property.

### The property type is wrong and PUT won't fix it

`type` is immutable. Delete the property and create a new one with the correct
type. (Soft-delete retains old values, but they will not surface under the new
property, which has a new ID.)

## Documentation Reference

Before writing or verifying any API call, confirm current endpoint paths and
field names against the cluster swagger (see
[SKILL.md](./SKILL.md#documentation-reference)):

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$DOMINO_API_HOST/api/taxonomy/swagger/doc.json"
```

- [SKILL.md](./SKILL.md) — skill overview, tags, namespaces, entity tagging
- [PROPERTY-VALUES.md](./PROPERTY-VALUES.md) — assigning values to entities
