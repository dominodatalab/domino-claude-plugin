#!/usr/bin/env bash
# Enforce the plugin version scheme on a pull request.
#
#   plugin.json "version" = YYYY.X-Y.N        (e.g. 2026.6-3.1)
#     YYYY  year of the release
#     X-Y   Domino line the content is correct for, written with a hyphen so it reads at a glance
#           (a floor: 6-3 = Domino 6.3 and later, incl. Cloud)
#     N     skill release counter, monotonic within a Domino line, never reused, never reset by year
#   git tag = release-<version>               (created by .github/workflows/tag-release.yml)
#
# Rules checked here (against the PR base ref):
#   1. version matches ^[0-9]{4}\.[0-9]+-[0-9]+\.[0-9]+$ (no leading zeros)
#   2. if any content path changed, version must differ from the base
#   3. version must not already exist as a release-<version> tag (never reuse)
#   4. on a release-X.Y base, the version's X-Y must equal the branch's X.Y
#   5. if the base already used scheme versions on the same X-Y line, N must increase;
#      the line (X.Y) and the year never go backwards, and the year is not in the future
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

head_version="$(jq -r '.version // empty' "$manifest")"
[ -n "$head_version" ] || fail "$manifest has no version"

if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
  fail "base ref '$base_ref' not found; fetch it first (git fetch origin <base>)"
fi
base_version="$(git show "$base_ref:$manifest" 2>/dev/null | jq -r '.version // empty' || true)"

# 1. format
if ! [[ "$head_version" =~ ^([0-9]{4})\.(0|[1-9][0-9]*)-(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  fail "version '$head_version' does not match YYYY.X-Y.N with no leading zeros (e.g. 2026.6-3.1)"
fi
head_year="${BASH_REMATCH[1]}"; head_line="${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"; head_n="${BASH_REMATCH[4]}"   # head_line is X.Y with a dot, to compare with release-X.Y

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
if [[ "$base_branch" =~ ^release-([0-9]+\.[0-9]+)$ ]]; then
  branch_line="${BASH_REMATCH[1]}"
  [ "$head_line" = "$branch_line" ] || fail "base branch $base_branch requires a $branch_line line, got '$head_version'"
fi

# 5. monotonic within the scheme, when the base is already on it
this_year="$(date +%Y)"
[ "$head_year" -le "$this_year" ] || fail "year $head_year is in the future (today is $this_year)"
line_num() { local x="${1%%.*}" y="${1#*.}"; echo $(( x * 1000 + y )); }   # 6.3 -> 6003, 6.10 -> 6010
if [[ "$base_version" =~ ^([0-9]{4})\.([0-9]+)-([0-9]+)\.([0-9]+)$ ]]; then
  base_year="${BASH_REMATCH[1]}"; base_line="${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"; base_n="${BASH_REMATCH[4]}"
  if [ "$head_version" != "$base_version" ]; then
    [ "$head_year" -ge "$base_year" ] || fail "year must not go backwards: base $base_version, head $head_version"
    if [ "$head_line" = "$base_line" ]; then
      [ "$head_n" -gt "$base_n" ] || fail "N must increase within the $head_line line: base $base_version, head $head_version"
    else
      [ "$(line_num "$head_line")" -gt "$(line_num "$base_line")" ] || fail "the Domino line must not go backwards: base $base_version, head $head_version"
      [[ "$base_branch" =~ ^release- ]] && fail "a release-X.Y branch never changes line: base $base_version, head $head_version"
    fi
  fi
fi

note "ok: $manifest version $head_version"
