# Import and export — taxonomy migration

Three endpoints handle taxonomy migration between Domino environments. The
file format is **CSV**, not JSON.

- `POST /rpc/export-to-file` — dump the current taxonomy as CSV
- `POST /rpc/validate-file` — dry-run an import file (multipart upload)
- `POST /rpc/import-from-file` — apply an import file (multipart upload)

All assume the configuration block from [SKILL.md](./SKILL.md#configuration):

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
BASE="$DOMINO_API_HOST/api/taxonomy/v1"
H="Authorization: Bearer $TOKEN"
```

## CSV format

```csv
namespace_label,namespace_description,tag_path,tag_description
Indication,Therapeutic area,Oncology,
Indication,Therapeutic area,Oncology/Breast_Cancer,Breast cancer subtype
Analysis,Type of analysis,Interim,Pre-planned interim analysis
Analysis,Type of analysis,Interim/Milestone_01,First interim milestone
```

- Each row describes one tag.
- `tag_path` uses `/` to express hierarchy. Parents are inferred from the
  path — you don't need a separate row per parent, but if the parent has its
  own description you should include it on its own row first.
- `namespace_description` repeats per row but only the first occurrence is
  used to set / update the namespace.
- Empty `tag_description` is allowed.

## Export

```bash
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
  -d '{}' "$BASE/rpc/export-to-file" \
  > taxonomy-export.csv
```

- Body is empty JSON `{}` — the export is unfiltered (the whole taxonomy).
- Response is `text/csv` with the header line shown above.
- Save to a file and check it into version control alongside whatever
  config drives your taxonomy, so changes are reviewable.

## Validate before import

Always dry-run before applying. Validation parses the CSV and runs
structural / length / depth checks without mutating state.

```bash
curl -s -X POST -H "$H" \
  -F "file=@taxonomy-import.csv" \
  "$BASE/rpc/validate-file"
# 200 → {"valid":true}
# 400 → {"message":"..."}                — file-level error (empty file, no `file` field)
# 422 → {"errors":[{"line":N,"message":"..."}]}  — per-row errors (all returned, not just first)
```

The endpoint expects **multipart form data**, not JSON. The form field name
is `file`. `-F "file=@<path>"` is the simplest way to send it from curl.

What the validator actually checks (verified 2026-05-11):

- ✅ File is non-empty and parseable as CSV
- ✅ Every row has exactly 4 columns
- ✅ Each tag-path segment ≤ `maxLabelLength` from `GET /config` (128 chars)
- ✅ Tag path depth ≤ `maxDepth` from `GET /config` (5 levels)
- ❌ **Does NOT check that the header row matches the expected column names.**
  A CSV whose first row is unrelated text passes with `{"valid":true}` and
  then imports the header as a real namespace called `namespace_label`. If
  you're building the CSV programmatically, double-check the header
  yourself before uploading.

## Import

```bash
curl -s -X POST -H "$H" \
  -F "file=@taxonomy-import.csv" \
  "$BASE/rpc/import-from-file"
# 200 → {"namespacesCreated":2,"tagsCreated":7}
```

- Same multipart pattern as `validate-file`.
- Existing namespaces / tags are reused when their labels match — the
  `*Created` counts only count net-new rows.
- Existing entity-tag bindings are not touched. Import only writes
  namespaces and tags.

## Migration recipes

### Promote dev taxonomy to prod

```bash
# On dev cluster
curl -s -X POST -H "$H_DEV" -H "Content-Type: application/json" \
  -d '{}' "$BASE_DEV/rpc/export-to-file" > taxonomy-dev.csv

# Inspect / scrub before promoting (e.g. remove sandbox namespaces)
grep -v '^claude-test-' taxonomy-dev.csv > taxonomy-prod.csv

# On prod cluster — validate first
curl -s -X POST -H "$H_PROD" -F "file=@taxonomy-prod.csv" \
  "$BASE_PROD/rpc/validate-file"
# Only proceed if {"valid":true}

curl -s -X POST -H "$H_PROD" -F "file=@taxonomy-prod.csv" \
  "$BASE_PROD/rpc/import-from-file"
```

### Round-trip backup

```bash
# Backup
curl -s -X POST -H "$H" -H "Content-Type: application/json" -d '{}' \
  "$BASE/rpc/export-to-file" > "taxonomy-backup-$(date +%Y%m%d).csv"

# Restore (idempotent — no-ops if everything already exists)
curl -s -X POST -H "$H" \
  -F "file=@taxonomy-backup-20260508.csv" \
  "$BASE/rpc/import-from-file"
```

### Scripted change

To make a change reviewable, edit the CSV in version control rather than
calling create/update endpoints by hand:

1. Pull current taxonomy: `POST /rpc/export-to-file > taxonomy.csv`
2. Open a PR editing `taxonomy.csv`
3. After review, on the target cluster:
   `POST /rpc/validate-file` → if valid, `POST /rpc/import-from-file`

This works well for additive changes. For destructive changes (deletes /
renames) use the targeted DELETE / PUT endpoints — import only adds.
