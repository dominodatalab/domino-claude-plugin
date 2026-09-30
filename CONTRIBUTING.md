# Contributing to Domino Data Lab Plugin

Thank you for your interest in contributing to the Domino Data Lab Plugin for Claude Code!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch

```bash
git clone https://github.com/YOUR_USERNAME/domino-data-lab-plugin.git
cd domino-data-lab-plugin
git checkout -b feature/your-feature-name
```

## Development Setup

Test the plugin locally with Claude Code:

```bash
claude --plugin-dir /path/to/domino-data-lab-plugin
```

## Plugin Structure

```
domino-data-lab-plugin/
├── .claude-plugin/plugin.json   # Plugin manifest (required)
├── skills/                      # Agent skills
├── commands/                    # Slash commands
├── agents/                      # Subagents
├── output-styles/               # Custom output styles
├── templates/                   # Code templates
└── hooks/                       # Example hooks
```

## Contribution Guidelines

### Adding a New Skill

1. Create a new directory under `skills/`
2. Add a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: domino-your-skill
description: Brief description of what this skill does. Include trigger keywords.
compatibility: Domino 6.3 and Domino Cloud. Requires DOMINO_API_HOST; in a run use DOMINO_API_PROXY or the localhost:8899 access-token endpoint, outside a run a Personal Access Token.
---

# Your Skill Name

Applies to Domino 6.3 and Domino Cloud.

## Description
Detailed description of the skill...
```

The directory name **must equal** `name` (agentskills.io rule; Codex and OpenCode key on
`name`, Antigravity on the folder).

3. Add the skill to `plugin.json`
4. Keep SKILL.md under 500 lines; use supporting files for details
5. Follow the [Skill Authoring Standards](#skill-authoring-standards) — auth
   pattern, host env vars, no `python-domino` SDK, verified endpoints,
   smoke-tested payloads

### Adding a New Command

1. Create a markdown file under `commands/`
2. Include description in frontmatter:

```yaml
---
description: What this command does
---

# /command-name

Usage and documentation...
```

3. Add the command to `plugin.json`

### Adding a New Agent

1. Create a markdown file under `agents/`
2. Include full frontmatter:

```yaml
---
name: domino-agent-name
description: When to use this agent. Use PROACTIVELY when...
tools: Read, Edit, Write, Bash, Grep, Glob
model: inherit
skills: skill1, skill2
---
```

3. Add the agent to `plugin.json`

## Skill Authoring Standards

These rules came out of PR #8 (NetApp Volumes skill) review. Skim them before
authoring or editing a `SKILL.md`. An audit of existing skills against these
rules lives in [SKILL_AUDIT.md](./SKILL_AUDIT.md).

### 1. Authenticate with the local token endpoint, not API keys

**NEVER use `DOMINO_USER_API_KEY`, not even as a fallback.** It is not a
secure pattern. The API keys are deprecated and will be removed in a future
Domino release. The local access-token endpoint is Domino's forward-looking
auth architecture for in-cluster execution.

Skills running inside Domino (workspace, job, app, model) should fetch a
short-lived bearer token from the local sidecar, or, where the platform injects
`DOMINO_API_PROXY` (JWT credential propagation), call `$DOMINO_API_PROXY/<path>` with
no `Authorization` header at all; the proxy adds the starting user's token. Outside a
run (laptop, CI) use a Personal Access Token or service-account token as a bearer. See
https://docs.domino.ai/cloud/reference/api/domino-api-authentication.

Do:

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
curl -H "Authorization: Bearer $TOKEN" "$DOMINO_API_HOST/api/..."
```

Don't (deprecated, will be removed):

```bash
curl -H "X-Domino-Api-Key: $DOMINO_USER_API_KEY" "$DOMINO_API_HOST/api/..."
```

Why: tokens fetched from the local endpoint are short-lived and scoped to
the current workspace/job. API keys are long-lived, leak into shell history
and process listings, tie requests to the user rather than the execution,
and are slated for removal. (PR #8: *"we should remove all the stuff here
about using X-Domino-Api-Key. We should have these examples fetch tokens
from localhost:8899/access-token"*.)

### 2. Use Domino-injected environment variables for hosts

| Variable | Use for |
|----------|---------|
| `$DOMINO_API_HOST` | Platform REST API (most endpoints) |
| `$DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT` | remotefs / NetApp APIs |
| `$DOMINO_PROJECT_ID`, `$DOMINO_PROJECT_OWNER`, `$DOMINO_PROJECT_NAME` | Project identifiers |
| `$DOMINO_RUN_ID` | Current job/workspace run ID |

Don't write `https://your-domino.com`, `<domino-host>`, or
`<your-domino-instance>` placeholders — they fail when the user copy-pastes
and they signal the example was never run.

### 3. Don't use the `python-domino` SDK in examples

The `python-domino` package wraps older API versions and lacks coverage for
newer features (e.g. NetApp volume mounts on jobs). Show REST + `curl` (or
`requests`) instead. (PR #8: *"a lot of its methods use older APIs and won't
support things like specifying NetApp volume mounts"*.)

Exception: the `domino-data-sdk` and `python-sdk` skills exist specifically to
document the SDK. They should clearly mark which methods are still supported
vs deprecated. All other skills should not pull `from domino import Domino`
into their examples.

### 4. Verify endpoints against live API docs before writing examples

Don't guess endpoints from memory. Use a two-tier approach:

**Check swagger first** for current endpoint paths and field names — the
cluster swagger always reflects the installed version. Get the cluster URL from
`$DOMINO_API_HOST`. Most endpoints are in the public API spec (no auth
needed); governance, taxonomy, and netapp-volumes swagger docs require a
bearer token from `localhost:8899/access-token`:

```bash
# Public API (no auth):
curl "$DOMINO_API_HOST/assets/public-api.json"

# Auth-required swagger (governance / netapp-volumes):
# These services are NOT routed through $DOMINO_API_HOST (internal Kubernetes URL).
# Derive the external cluster URL from the JWT iss claim — works in any workspace type.
TOKEN=$(curl -s http://localhost:8899/access-token)
CLUSTER_URL=$(echo $TOKEN | cut -d'.' -f2 | python3 -c "
import sys, base64, json, re
p = sys.stdin.read().strip()
p += '=' * (-len(p) % 4)
print(re.sub(r'/auth/realms/.*', '', json.loads(base64.b64decode(p))['iss']))
")
curl -H "Authorization: Bearer $TOKEN" "$CLUSTER_URL/<service>/swagger/doc.json"
```

**Then check public docs** (`docs.dominodatalab.com/api_guide`) for workflow
context, field explanations, and richer examples when the swagger schemas
alone aren't sufficient.

PR #8 caught a wrong jobs endpoint (`/api/jobs/v1/runs` → `/api/jobs/v1/jobs`)
that had been carried forward from an older version.

### 5. Smoke-test payloads against the live API

Required fields and field names drift between releases. Examples from PR #8
that took multiple iterations to get right:

- `commandToRun` → `runCommand`
- `externalVolumeMounts` → `netAppVolumeIds`
- `environmentId` is required on `POST /api/jobs/v1/jobs` and was missing

Run each documented payload at least once against a live Domino instance and
confirm a 2xx before merging. Note your test result (status code, any
clean-up steps) in the PR description.

### 6. `.gitignore` edits are additive

If a PR removes lines from `.gitignore`, justify it in the PR description.
Accidental removals of existing rules will be flagged in review.

### 7. Declare which Domino versions a skill applies to

The plugin targets **Domino 6.3 (self-managed)** and **Domino Cloud**, and `main` must be
correct for both. Every `SKILL.md`:

- carries a `compatibility:` frontmatter field (agentskills.io optional field, ≤ 500
  characters), for example
  `compatibility: Domino 6.3 and Domino Cloud. Requires DOMINO_API_HOST; in a run use DOMINO_API_PROXY or the localhost:8899 access-token endpoint, outside a run a Personal Access Token.`
- opens its body with a one-line scope statement: `Applies to Domino 6.3 and Domino Cloud.`
- if behaviour genuinely differs between the two targets, includes a short **"Which path
  applies"** section that reads `GET $DOMINO_API_HOST/version` and branches on the result.
  Only add this where behaviour differs; do not add it everywhere.
- never tells the agent to reinstall, downgrade or repin the plugin. If the deployment is
  older than 6.3, say the skill targets 6.3 and later and point to
  `docs.dominodatalab.com` for that version.

Verify cited API routes against **both** published specs:
`https://docs.domino.ai/api-specs/6.3/public-api.json` and
`https://docs.domino.ai/api-specs/cloud/public-api.json`. Every Domino deployment from 6.3
also serves its own cluster-specific API reference at `https://<domino-domain>/docs`
(Scalar, unauthenticated), with one OpenAPI document per service under
`/docs/openapi/`: `openapi-public.json` is the deployment's Public API, and
`openapi-internal.json` is the **Domino Internal API**, where the `/v4/*` routes live.
`$DOMINO_API_HOST/assets/public-api.json` is only a subset of the public one and omits
governance, taxonomy, model monitoring, NetApp volumes and dataset file routes, so do not
treat it as complete. Routes that exist only in the Internal API (`/v4/*`) are not part of
the Public API and are not versioned for external use: prefer the `/api/...` equivalent,
and where none exists label the call **internal API, may change between Domino versions**
at the point of use. The
verified divergence between the two targets is recorded in `coverage/COMPAT.md` (maintainers’ audit workspace, not yet in this repo).

Nothing about versions goes in `description`; it is loaded for every skill on every turn
and exists for triggering only.

### 8. Author skill content with a Fable-class or Astra-class model, and attest to it

Skill content is instructions that another model will follow. Authoring it with a weaker
model produces plausible-looking procedure that is wrong in the details, which is exactly
the failure the coverage audit found across the repo (invented SDK methods, invented YAML
formats, routes that do not exist).

- New skills and substantive rewrites **must** be authored with a Fable-class or
  Astra-class model. Drafting with a smaller model and then polishing does not qualify.
- The PR template asks for the model identifier and a human attestation. The person
  opening the PR is attesting; do not have an agent tick the box.
- Small edits to existing content (a corrected field name, a fixed link) do not require
  the attestation, but still require verification against the spec and SDK source.

### 9. Keep internal references out of a public repository

This repository is public and its skills are installed into customer environments. Skill
content must not contain links to Jira, Confluence, Slack or internal repositories, ticket
keys, internal ranking artefacts, or paths to scripts users cannot obtain. If an example
script is worth citing, add it to the repo under the skill (for example
`skills/<name>/examples/`).

### 10. Bump `plugin.json` on every content change, using the release scheme

Claude Code copies a marketplace plugin into its cache under the `plugin.json` `version`
string and re-reads it only when that string changes. Any change under `skills/`, `commands/`,
`agents/`, `templates/`, `mcp-servers/`, `output-styles/`, `hooks/`, `bin/`, `workflows/`,
`themes/`, `monitors/`, `.mcp.json`, `.lsp.json`, `settings.json` or `plugin.json` itself must
therefore bump `version`, or nothing reaches installed copies. CI (`scripts/check-version.sh`) rejects a PR
that changes those paths without a bump.

The version is **`YYYY.X-Y.N`**, for example `2026.6-3.1`:

| Part | Meaning |
|---|---|
| `YYYY` | Year of the release. |
| `X-Y` | The Domino line the content is correct for, written with a hyphen so the four parts read at a glance (`6-3` is Domino 6.3), as a **floor**: `6.3` means Domino 6.3 and later, including Domino Cloud. `main` carries the current floor. |
| `N` | Skill release counter. Increases with every release on that `X.Y` line, is never reused, and is **not** reset by the year (`2026.6-3.14` is followed by `2027.6-3.15`). |

The git tag `release-YYYY.X-Y.N` is created automatically from the manifest on every push to
`main` or a `release-*` branch (`.github/workflows/tag-release.yml`), so tag and manifest
always agree. Plugin version is independent of Domino's own version numbers; `X.Y` states
compatibility, not identity.

## Release branches, tags and backports

Three things carry a version, and they are deliberately different:

| Object | Form | Who reads it |
|---|---|---|
| Branch | `main`, `release-6.3`, `release-6.4` … | The Domino Standard Environment (DSE) update script, which runs at Workspace launch and resolves **by exact branch name**: `release-X.Y.Z`, then `release-X.Y`, then `main`, from the cluster's `DOMINO_VERSION`. Any other branch name is invisible to it. |
| Tag | `release-YYYY.X-Y.N` | Humans, and admins pinning a Workspace to one release through the script's override argument (`DOMINO_CLAUDE_SKILLS_BRANCH`), which accepts a branch, tag or commit. |
| `plugin.json` `version` | `YYYY.X-Y.N` | Claude Code, to decide whether an installed copy is stale. |

Rules:

- `main` is correct for every supported target (Domino 6.3 and Cloud today). Version-specific
  behaviour is gated inside the skill, not by branch. `X-Y` in the version is the **floor** of
  what the content is correct for, so `main` carries `YYYY.6-3.N` for as long as it is still
  correct for 6.3, even after 6.4 ships.
- A `release-X.Y` branch exists only once `main`'s floor has moved past `X.Y`. Until then a
  Domino `X.Y` cluster resolves to `main`, which is correct for it. When the floor moves (say
  `main` drops 6.3 and becomes `YYYY.6-4.N`), cut `release-6.3` from the last `6.3` commit;
  it then receives cherry-picks only, its versions stay on the `6.3` line, and it is never
  created for a Domino version that has not shipped (Cloud runs ahead of self-managed and
  would freeze on it). This keeps one meaning for `X.Y`: the branch line and the floor are the
  same number, and no two branches share a counter.
- **Backport** = cherry-pick the fix onto `release-X.Y`, bump `N` on that line, open the PR
  against the branch. CI checks that the version's `X.Y` equals the branch's. The tag follows
  automatically on merge.
- Never reuse a version string; a reused string points Claude at the old cached copy. A
  `git revert` of a content change is itself a content change and needs its own bump. Any edit
  to `plugin.json` counts as content.
- If `tag-release` fails with "already exists at a different commit", two PRs landed with the
  same version (usually a stale green check). Recover with a bump-only PR to the next `N`;
  do not move or delete the existing tag.
- The version check is only a gate if the repository requires it: maintainers keep
  `Version check / version` as a required status check with "require branches to be up to
  date" on `main` and every `release-*` branch, so a PR re-runs against the moved base.

How each channel receives a release:

- **Anthropic official marketplace**: the entry pins `main` by commit sha. Anthropic advances
  the pin on its own schedule (an automated bump job that is sometimes paused), and Claude
  Code installs the new copy once the manifest string differs. After a release, check the
  `sha` for `dominodatalab` in `anthropics/claude-plugins-official` and request a bump if it
  lags.
- **Domino DSE Workspaces**: the launch script checks out the resolved branch in the clone,
  but Claude Code loads a cache copy keyed by version, so the checkout alone changes nothing
  (verified on 2.1.284). The copy is refreshed only when something recomputes the version:
  `claude plugin update`, or Claude Code's background auto-update, which runs a few minutes
  into an interactive session, refreshes every marketplace that has auto-update **on**, and
  applies the new copy at the next launch. Auto-update is **off by default for every
  marketplace except Anthropic's**, including the image's local `domino-marketplace`, so
  the image must turn it on (`autoUpdate: true` on the marketplace's `extraKnownMarketplaces`
  settings entry, or the `/plugin` Marketplaces toggle) or the launch script must run
  `claude plugin update domino-claude-plugin@domino-marketplace` after the checkout. With
  either in place, a version bump on the resolved branch reaches a Workspace one launch
  later. Until then a Workspace keeps the version its image was built with. Claude Code's
  documentation also describes relative-path plugins from a locally added marketplace as
  loading in place without a version bump; that is not the observed behaviour on 2.1.284.
- **`--plugin-dir`**: loads in place; `git pull` or checking out a tag is the update.

`scripts/verify-update-flow.sh` reproduces the DSE install layout against a throwaway
marketplace and asserts the caching behaviour these rules rest on. Run it when Claude Code
changes its plugin loading; if its first assertion fails, Claude has started loading this
layout in place, and the DSE paragraph above needs updating.

## Code Style

- Use consistent YAML frontmatter format
- Include code examples with proper language tags
- Use tables for reference documentation
- Keep descriptions actionable and specific

## Testing Changes

Before submitting:

1. Verify all referenced files exist
2. Test skills trigger correctly
3. Verify commands work as documented
4. Check for broken internal links
5. Smoke-test every API payload documented in a skill against a live Domino
   instance and record the result in the PR description (see
   [Skill Authoring Standards #5](#5-smoke-test-payloads-against-the-live-api))

```bash
# Verify file structure
find skills -name "SKILL.md" | wc -l  # Should match plugin.json count

# Check for broken links
grep -r "\](\./" --include="*.md" | head -20
```

## Pull Request Process

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) is the checklist; fill every section.
Reviewers will send back PRs with unticked required sections.

1. Link the Jira ticket. Skills work lives under the DOCS-6840 epic.
2. Declare Domino version applicability and confirm both specs were checked (standard 7).
3. For new or rewritten skill content, name the model used and tick the attestation
   (standard 8).
4. Confirm no internal references (standard 9) and bump `plugin.json` to the next `YYYY.X-Y.N` (standard 10). CI fails the PR otherwise.
5. Update the README skill table and counts for any added, renamed or removed component.
6. Describe what you tested and against which deployment version.
7. Request review from a maintainer. One approving review and passing checks are required
   to merge. Note in the PR if the change must be cherry-picked to `release-6.3`.

## Reporting Issues

Please include:
- Claude Code version
- Plugin version
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue for bugs or feature requests
- See [Domino Documentation](https://docs.dominodatalab.com/) for platform questions
