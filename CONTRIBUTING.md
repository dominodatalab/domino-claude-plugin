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
---

# Your Skill Name

## Description
Detailed description of the skill...
```

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
short-lived bearer token from the local sidecar.

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

1. Update the README if adding new features
2. Add your changes to CHANGELOG (if it exists)
3. Ensure all tests pass
4. Request review from maintainers

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
