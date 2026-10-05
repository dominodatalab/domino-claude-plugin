#!/usr/bin/env bash
# Enforce the plugin version scheme on a pull request.
#
#   plugin.json "version" = YYYY.DDD.N          (e.g. 2026.603.3)
#     YYYY  year of the release
#     DDD   Domino line code: the Domino major followed by the two-digit minor
#           (603 = Domino 6.3, 610 = 6.10, 700 = 7.0). A floor: 603 = 6.3 and later, incl. Cloud.
#           Three dotted numeric parts so semver-aware tooling parses and orders it correctly.
#     N     skill release counter, monotonic within a Domino line, never reused, never reset by year
#   git tag = release-<version>                 (created by .github/workflows/tag-release.yml)
#
#   Releases before 2026-10 used YYYY.X-Y.N (2026.6-3.1, 2026.6-3.2). Those tags stay; this
#   script still reads that form on the base so the monotonic rules hold across the change.
#
# Rules checked here (against the PR base ref):
#   1. version matches ^[0-9]{4}\.[1-9][0-9]{2,}\.(0|[1-9][0-9]*)$ (no leading zeros)
#   2. if any content path changed, version must differ from the base
#   3. version must not already exist as a release-<version> tag (never reuse)
#   4. on a release-X.Y base, the version's DDD must equal X*100+Y
#   5. if the base already used scheme versions on the same line, N must increase;
#      the line and the year never go backwards, and the year is not in the future
#   6. on the integration branch `develop`, the version must EQUAL the base: feature PRs do
#      not mint releases; the develop -> main promotion PR carries the one bump
#
# Usage: scripts/check-version.sh <base-ref>        e.g. scripts/check-version.sh origin/main
# Exit 0 = ok, 1 = violation, 2 = usage/tooling error.
set -euo pipefail

base_ref="${1:-}"
[ -n "$base_ref" ] || { echo "usage: $0 <base-ref>" >&2; exit 2; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 2; }

manifest=".claude-plugin/plugin.json"
content_paths=(skills commands agents templates mcp-servers output-styles hooks bin workflows themes monitors .mcp.json .lsp.json settings.json "$manifest")

fail() { echo "::error::$*" >&2; exit 1; }
note() { echo "$*"; }
line_of() { echo "$(( $1 / 100 )).$(( $1 % 100 ))"; }   # 603 -> 6.3, 610 -> 6.10

# Parse a version into year, line code, N. Accepts the current form and the pre-2026-10 form.
# Sets p_year p_code p_n; returns 1 if the string is neither.
parse_version() {
  if [[ "$1" =~ ^([0-9]{4})\.([1-9][0-9]{2,})\.(0|[1-9][0-9]*)$ ]]; then
    p_year="${BASH_REMATCH[1]}"; p_code="${BASH_REMATCH[2]}"; p_n="${BASH_REMATCH[3]}"
  elif [[ "$1" =~ ^([0-9]{4})\.([0-9]+)-([0-9]+)\.([0-9]+)$ ]]; then
    p_year="${BASH_REMATCH[1]}"; p_code=$(( BASH_REMATCH[2] * 100 + BASH_REMATCH[3] )); p_n="${BASH_REMATCH[4]}"
  else
    return 1
  fi
}

head_version="$(jq -r '.version // empty' "$manifest")"
[ -n "$head_version" ] || fail "$manifest has no version"

if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
  fail "base ref '$base_ref' not found; fetch it first (git fetch origin <base>)"
fi
base_version="$(git show "$base_ref:$manifest" 2>/dev/null | jq -r '.version // empty' || true)"

# 1. format (the current form only; the legacy form is accepted on the base, never on the head)
if ! [[ "$head_version" =~ ^([0-9]{4})\.([1-9][0-9]{2,})\.(0|[1-9][0-9]*)$ ]]; then
  fail "version '$head_version' does not match YYYY.DDD.N with no leading zeros (e.g. 2026.603.3; DDD = Domino major + two-digit minor)"
fi
head_year="${BASH_REMATCH[1]}"; head_code="${BASH_REMATCH[2]}"; head_n="${BASH_REMATCH[3]}"
head_line="$(line_of "$head_code")"

# 6. integration branch: no bumps here
if [ "${base_ref#origin/}" = "develop" ]; then
  if [ "$head_version" != "$base_version" ]; then
    fail "develop is the integration branch and keeps the version frozen (base $base_version, head $head_version). Bump N only in the develop -> main release PR."
  fi
  note "ok: integration branch develop, version unchanged at $head_version"
  exit 0
fi

# 2. bump required when content changed
changed="$(git diff --name-only "$base_ref"...HEAD -- "${content_paths[@]}" || git diff --name-only "$base_ref" HEAD -- "${content_paths[@]}")"
if [ -n "$changed" ]; then
  if [ "$head_version" = "$base_version" ]; then
    fail "content changed but $manifest version is still '$head_version'. Bump N (or the line) so installed copies receive this change:
$(echo "$changed" | sed 's/^/  - /')"
  fi
  note "content changed; version $base_version -> $head_version"
else
  note "no content paths changed; version bump not required (version is $head_version)"
fi

# 3. never reuse: tag must not exist for a *new* version
if [ "$head_version" != "$base_version" ]; then
  if git ls-remote --exit-code --tags origin "refs/tags/release-$head_version" >/dev/null 2>&1 \
     || git rev-parse --verify --quiet "refs/tags/release-$head_version" >/dev/null; then
    fail "tag release-$head_version already exists; versions are never reused"
  fi
fi

# 4. release-X.Y base must keep its line
base_branch="${base_ref#origin/}"
if [[ "$base_branch" =~ ^release-([0-9]+)\.([0-9]+)$ ]]; then
  branch_code=$(( BASH_REMATCH[1] * 100 + BASH_REMATCH[2] ))
  [ "$head_code" -eq "$branch_code" ] || fail "base branch $base_branch requires line code $branch_code ($(line_of "$branch_code")), got '$head_version' (line $head_line)"
fi

# 5. monotonic within the scheme, when the base is already on it (either form)
this_year="$(date +%Y)"
[ "$head_year" -le "$this_year" ] || fail "year $head_year is in the future (today is $this_year)"
if parse_version "$base_version"; then
  base_year="$p_year"; base_code="$p_code"; base_n="$p_n"
  if [ "$head_version" != "$base_version" ]; then
    [ "$head_year" -ge "$base_year" ] || fail "year must not go backwards: base $base_version, head $head_version"
    if [ "$head_code" -eq "$base_code" ]; then
      [ "$head_n" -gt "$base_n" ] || fail "N must increase within the $head_line line: base $base_version, head $head_version"
    else
      [ "$head_code" -gt "$base_code" ] || fail "the Domino line must not go backwards: base $base_version ($(line_of "$base_code")), head $head_version ($head_line)"
      [[ "$base_branch" =~ ^release- ]] && fail "a release-X.Y branch never changes line: base $base_version, head $head_version"
    fi
  fi
fi

note "ok: $manifest version $head_version (Domino line $head_line, release $head_n)"
