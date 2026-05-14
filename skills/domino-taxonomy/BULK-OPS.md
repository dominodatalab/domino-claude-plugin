# Bulk operations and tag merging

Three endpoints handle bulk lifecycle work on a Domino taxonomy:

- `POST /tags/bulk-delete` — delete many tags by ID
- `POST /namespaces/bulk-delete` — delete many namespaces (cascades through their tags)
- `POST /rpc/merge-tags` — collapse duplicates into one canonical tag

All assume the configuration block from [SKILL.md](./SKILL.md#configuration):

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"
```

## Bulk delete tags

```bash
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"ids":["<tag-1>","<tag-2>","<tag-3>"]}' \
  "$BASE/tags/bulk-delete"
# 200 → {"deletedCount":3}
```

- `ids` is required and must contain at least one ID.
- Tags that don't exist are silently skipped — `deletedCount` reflects the
  actual deletions.
- Entities tagged with these tags lose those tags as a side effect. Use this
  when you're sure you no longer need the tags anywhere.

## Bulk delete namespaces

```bash
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"ids":["<ns-1>","<ns-2>"]}' \
  "$BASE/namespaces/bulk-delete"
# 200 → {"deletedCount":2}
```

Unlike single `DELETE /namespaces/{id}`, the bulk endpoint cascades through
each namespace's tags and entity-tag bindings. Reach for this when you want
to remove an entire dimension of your taxonomy.

## Merge tags

Use to collapse duplicates: every entity tagged with a `sourceTagIds` tag
is re-tagged with the `targetTagId`, then the source tags are deleted.

```bash
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{
        "sourceTagIds":["<dup-1>","<dup-2>"],
        "targetTagId":"<canonical>"
      }' \
  "$BASE/rpc/merge-tags"
# 200 → {
#   "targetTag":{"id":"<canonical>","label":"..."},
#   "mergedCount":2,
#   "reassignedEntities":17
# }
```

- `sourceTagIds` and `targetTagId` are both required.
- All source tags must live in the same namespace as the target.
- `reassignedEntities` is the number of distinct entity-tag bindings that
  were rewritten to point at the target.
- Source tags are deleted on success.

## Migration patterns

### Bulk-tagging during onboarding

Drive `POST /rpc/tag-entity` from a CSV of `(entityType, entityId, tagId)`
rows. There is no batch tag-entity endpoint, so loop one entity at a time.

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"

while IFS=, read -r etype eid tag; do
  curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{\"entityType\":\"$etype\",\"entityId\":\"$eid\",\"tagIds\":[\"$tag\"]}" \
    "$BASE/rpc/tag-entity" > /dev/null && echo "tagged $etype/$eid"
done < onboarding.csv
```

For thousands of rows, parallelize with `xargs -P` and consider re-fetching
the token periodically — bearer tokens expire.

### De-duplicating after a free-form tagging period

When users have created variant labels (`Phase 1`, `phase-1`, `phase_1`),
audit and merge:

1. List all tags in a namespace: `GET $BASE/tags?namespaceId=<id>&limit=200`
2. Group by normalized label, identify duplicates
3. Pick one canonical ID per group
4. Call `POST $BASE/rpc/merge-tags` per group with sources → target

`mergedCount` and `reassignedEntities` from the response let you log audit
trail rows for the change.

### Cleaning up an entire experiment namespace

When a project / sandbox namespace is no longer needed:

```bash
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{"ids":["<sandbox-ns-id>"]}' \
  "$BASE/namespaces/bulk-delete"
```

This removes the namespace, all its tags, and any entity-tag bindings
pointing at those tags. There is no undo — confirm with the user first
when scripting against a shared environment.
