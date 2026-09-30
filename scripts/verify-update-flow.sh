#!/usr/bin/env bash
# End-to-end check of how Claude Code delivers this plugin through a local-directory
# marketplace, mirroring the Domino Standard Environment (DSE) layout:
#
#   ~/.claude/marketplaces/domino/.claude-plugin/marketplace.json  (source: ./plugins/domino-claude-plugin)
#   ~/.claude/marketplaces/domino/plugins/domino-claude-plugin      (git clone)
#   claude plugin marketplace add <dir> && claude plugin install domino-claude-plugin@domino-marketplace
#
# Verified behaviour (Claude Code 2.1.284, 2026-09-28), asserted below:
#   A. install copies the plugin into the cache; it is not loaded in place from the clone
#   B. a `git checkout` of another commit in the clone is invisible to Claude
#   C. `claude plugin update` with an unchanged plugin.json version does nothing
#   D. changing the version string makes `update` copy the clone's current state
#
# If assertion A ever fails (install path is the clone itself), Claude Code has started loading
# this layout in place and the DSE update script's checkout becomes effective on its own; update
# CONTRIBUTING.md "Release branches, tags and backports" accordingly.
#
# Usage: scripts/verify-update-flow.sh [git-url-or-path]      default: this repository's origin
# Requires: claude (Claude Code CLI), git, python3. Uses a throwaway marketplace named
# dse-mirror-verify and removes it on exit. Does not touch other installed plugins.
set -euo pipefail

repo="${1:-$(git -C "$(dirname "$0")/.." remote get-url origin)}"
mkt_name="dse-mirror-verify"
plugin_name="domino-claude-plugin"
work="$(mktemp -d /tmp/dse-mirror.XXXXXX)"
fails=0

log()  { printf '[verify-update-flow] %s\n' "$*"; }
pass() { printf '  PASS %s\n' "$*"; }
fail() { printf '  FAIL %s\n' "$*"; fails=$((fails+1)); }

cleanup() {
  claude plugin marketplace remove "$mkt_name" >/dev/null 2>&1 || true
  rm -rf "$HOME/.claude/plugins/cache/$mkt_name" "$work"
}
trap cleanup EXIT

record() {  # prints installPath|version|gitCommitSha for our test plugin ('|' keeps empty fields in place)
  python3 - "$mkt_name" "$plugin_name" <<'EOF'
import json, os, sys
mkt, name = sys.argv[1], sys.argv[2]
p = os.path.expanduser('~/.claude/plugins/installed_plugins.json')
d = json.load(open(p)).get('plugins', {})
for k, v in d.items():
    if k == f"{name}@{mkt}":
        r = v[0]; print(r.get('installPath',''), r.get('version',''), r.get('gitCommitSha',''), sep='|'); break
EOF
}

command -v claude >/dev/null || { echo "claude CLI not found" >&2; exit 2; }
log "Claude Code $(claude --version 2>/dev/null | head -1)"

mkdir -p "$work/marketplaces/domino/.claude-plugin" "$work/marketplaces/domino/plugins"
clone="$work/marketplaces/domino/plugins/$plugin_name"
git clone -q "$repo" "$clone"
cat > "$work/marketplaces/domino/.claude-plugin/marketplace.json" <<JSON
{"name":"$mkt_name","owner":{"name":"verify"},"plugins":[{"name":"$plugin_name","description":"update-flow verification","source":"./plugins/$plugin_name","category":"development"}]}
JSON

head_sha="$(git -C "$clone" rev-parse HEAD)"
# find an older commit and a skill file that exists in both commits with different content
# (M = modified), so the two blobs are comparable; walk back up to 25 commits
marker=""; old_sha=""
for n in $(seq 2 25); do
  cand="$(git -C "$clone" rev-parse --verify --quiet "HEAD~$n" || true)"; [ -n "$cand" ] || break
  marker="$(git -C "$clone" diff --name-only --diff-filter=M "$cand" HEAD -- skills | head -1)"
  if [ -n "$marker" ]; then old_sha="$cand"; break; fi
done
[ -n "$marker" ] || { echo "no skill file is modified within the last 25 commits; cannot build a marker" >&2; exit 2; }
log "marker file (differs between ${old_sha:0:7} and HEAD): $marker"

log "install from local marketplace"
claude plugin marketplace add "$work/marketplaces/domino" >/dev/null
claude plugin install "$plugin_name@$mkt_name" >/dev/null
IFS='|' read -r install_path version1 sha1 <<<"$(record)"
log "installed: version=$version1 sha=$sha1 path=$install_path"

# A. copied, not in place
if [ -d "$install_path" ] && [ ! -L "$install_path" ] && [ "$(cd "$install_path" && pwd -P)" != "$(cd "$clone" && pwd -P)" ]; then
  pass "A: install is a cache copy (${install_path#"$HOME"/})"
else
  fail "A: install path is the clone or a symlink to it; Claude loads this layout in place now"
fi

# C. same version -> no update (run before any checkout so the clone's manifest still equals the installed version)
out="$(claude plugin update "$plugin_name@$mkt_name" 2>&1 || true)"
IFS='|' read -r install_path_c version2 _ <<<"$(record)"
if [ "$version2" = "$version1" ] && [ "$install_path_c" = "$install_path" ]; then pass "C: update with unchanged version '$version1' is a no-op"; else fail "C: update changed state with an unchanged version: version=$version2 path=$install_path_c ($out)"; fi

# B. checkout in the clone is invisible. Pin the old commit's manifest version back to the installed one
# so that only content differs (older commits may carry a different version string).
git -C "$clone" checkout -q "$old_sha"
python3 - "$clone/.claude-plugin/plugin.json" "$version1" <<'EOF'
import json, sys
p, v = sys.argv[1], sys.argv[2]; d = json.load(open(p)); d['version'] = v; json.dump(d, open(p, 'w'), indent=2)
EOF
head_blob="$(git -C "$clone" show "$head_sha:$marker" | shasum | cut -c1-12)"
cache_blob="$( [ -f "$install_path/$marker" ] && shasum "$install_path/$marker" | cut -c1-12 || echo missing)"
if [ "$cache_blob" = "$head_blob" ]; then pass "B: after checking out ${old_sha:0:7} in the clone, the cache still serves HEAD content"; else fail "B: cache content changed after a bare checkout"; fi
out="$(claude plugin update "$plugin_name@$mkt_name" 2>&1 || true)"
cache_blob_b="$( [ -f "$install_path/$marker" ] && shasum "$install_path/$marker" | cut -c1-12 || echo missing)"
if [ "$cache_blob_b" = "$head_blob" ]; then pass "B2: update after the checkout, with the version unchanged, still serves HEAD content"; else fail "B2: update picked up the checkout without a version change ($out)"; fi

# D. bumped version -> update copies the clone's current state (the older commit)
python3 - "$clone/.claude-plugin/plugin.json" <<'EOF'
import json, sys, re
p = sys.argv[1]; d = json.load(open(p)); v = d['version']
# scheme version: bump N by 1000 so it can never collide with a real release; anything else: append a marker
d['version'] = re.sub(r'\.(\d+)$', lambda m: '.' + str(int(m.group(1)) + 1000), v) if re.match(r'^\d{4}\.\d+-\d+\.\d+$', v) else v + '.verify'
json.dump(d, open(p, 'w'), indent=2)
EOF
bumped="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$clone/.claude-plugin/plugin.json")"
claude plugin update "$plugin_name@$mkt_name" >/dev/null 2>&1 || true
IFS='|' read -r install_path2 version3 sha3 <<<"$(record)"
old_blob="$(git -C "$clone" show "$old_sha:$marker" | shasum | cut -c1-12)"   # content at the old commit (manifest edits do not touch the marker)
cache_blob2="$( [ -f "$install_path2/$marker" ] && shasum "$install_path2/$marker" | cut -c1-12 || echo missing)"
if [ "$version3" = "$bumped" ] && [ "$cache_blob2" = "$old_blob" ]; then
  pass "D: bumping to '$bumped' made update copy the clone's current state (commit ${sha3:0:7})"
else
  fail "D: expected version $bumped serving $old_sha content; got version=$version3 sha=$sha3"
fi

echo
if [ "$fails" -eq 0 ]; then log "all assertions passed: Claude Code caches by plugin.json version; the DSE checkout alone does not deliver updates"; exit 0
else log "$fails assertion(s) failed; re-read coverage/COMPAT.md delivery mapping and DOCS-6804"; exit 1; fi
