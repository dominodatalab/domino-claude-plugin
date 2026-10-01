# Working on domino-claude-plugin

Instructions for agents and people changing **this repository**. Claude Code, Codex and
OpenCode all read this file. Rules for what a skill may tell an agent at runtime live in the
skills and in `CONTRIBUTING.md`.

## What this is

A Claude Code plugin (`.claude-plugin/plugin.json`, name `dominodatalab`) whose `skills/` are
also consumed by Codex, Copilot, OpenCode and Antigravity, which read the same agentskills.io
layout from their own skills directories. Content here ships to customer environments from a
**public** repository. Two facts drive most rules below:

1. Claude Code installs a marketplace plugin as a cache copy keyed by the `plugin.json`
   `version` string and re-reads it only when that string changes. A content change without a
   version change ships to nobody. (Verified on Claude Code 2.1.284; it contradicts the docs'
   description of local-directory marketplaces, so re-run `scripts/verify-update-flow.sh`
   when Claude Code changes and update CONTRIBUTING if it stops holding.)
2. One tree targets **Domino 6.3 (self-managed) and Domino Cloud**. Where the product differs,
   the skill branches at runtime; content is never forked per version.

## Layout

| Path | Contents |
|---|---|
| `skills/<name>/SKILL.md` | One skill per directory. Reference files sit beside `SKILL.md`. |
| `agents/`, `commands/`, `templates/`, `output-styles/` | Claude-only components |
| `hooks/` | Documentation only today; no `hooks.json` is shipped |
| `mcp-servers/` | Bundled MCP server. Root `.mcp.json` currently points at a Workspace image path, not here; fixing that is an open task |
| `.claude-plugin/plugin.json` | Manifest. `version` is release state; see the rules below before touching it |
| `scripts/check-version.sh` | The CI version gate; run it locally before opening a PR |
| `scripts/verify-update-flow.sh` | Reproduces how Claude installs and updates this plugin |
| `.github/` | PR template, `version-check.yml`, `tag-release.yml`, `CODEOWNERS` |

## Branches and versions

| Branch | Role | Version rule |
|---|---|---|
| `develop` | Integration branch. All content PRs target it. | `plugin.json` `version` unchanged; CI fails a bump here |
| `main` | What ships. The Anthropic marketplace pins a commit on it; Domino Workspaces fall back to it | Changed only by the `develop` → `main` promotion PR, which bumps once and is tagged on merge |
| `release-X.Y` | Snapshot for a Domino line, cut only when `main` stops being correct for it | Cherry-picks only; version stays on that line |

- Version format is `YYYY.X-Y.N`, for example `2026.6-3.1`: year, Domino line as a floor
  (`6-3` = 6.3 and later including Cloud), release counter. `N` never repeats and never resets.
  CI creates the tag `release-<version>` on merge to `main` or `release-*`.
- Never create a branch named `release-*` for anything but a real snapshot. The Domino
  Workspace updater resolves `release-X.Y.Z`, `release-X.Y`, `main` by exact name and would
  serve an integration branch to every matching cluster on its next launch.
- Repo mechanics only (`.github/`, `scripts/`, `CONTRIBUTING.md`, `README.md`, this file) may
  target `main` directly; they touch no content paths, so no bump and no tag.
- The marketplace pin advances on Anthropic's schedule, not on merge. After a release, check
  the `sha` for `dominodatalab` in `anthropics/claude-plugins-official`.
- Run `scripts/check-version.sh origin/<your PR's base branch>` before pushing. It applies
  the rules CI applies and prints why it fails.

## Requirements for skill content

Skills here have shipped invented REST routes, invented YAML formats and non-existent SDK
methods. Each was plausible and each was wrong, so verification is not optional. The detailed
standards are CONTRIBUTING.md 1, 4, 7, 9 and 10; the requirements are:

- Every REST route must exist in the published spec for each Domino version the skill claims:
  `https://docs.domino.ai/api-specs/6.3/public-api.json` and
  `https://docs.domino.ai/api-specs/cloud/public-api.json`. For a specific deployment, use its
  own reference at `https://<domino-domain>/docs` (`/docs/openapi/openapi-public.json`);
  `$DOMINO_API_HOST/assets/public-api.json` is a subset and misses whole services.
- `/v4/*` routes are the Domino Internal API (documented per cluster under `/docs`, absent from
  the Public API). Use the `/api/...` equivalent; where none exists, label the call
  "internal API, may change between Domino versions" where it appears.
- Product behaviour comes from docs.domino.ai (`/cloud/...` and `/6.3/...`; `llms.txt` indexes
  every page, and any page is Markdown with `.md` appended). Cite docs.domino.ai, not
  `docs.dominodatalab.com/en/latest`.
- `python-domino` methods must exist in `domino/domino.py` on `master` of
  `github.com/dominodatalab/python-domino`.
- Authentication: in a run, `DOMINO_API_PROXY` with no header or a bearer from
  `http://localhost:8899/access-token`; outside a run, a Personal Access Token or service
  account token. Legacy user API keys are described as deprecated, never recommended.
- Every `SKILL.md` must carry `compatibility:` frontmatter and open its body with
  `Applies to Domino 6.3 and Domino Cloud.` Add a "Which path applies" section, keyed on
  `GET $DOMINO_API_HOST/version`, only where behaviour differs between the two. Never tell an
  agent to reinstall, downgrade or repin the plugin.
- `name` in frontmatter must equal the directory name; `description` under 1,024 characters
  and about triggering only, nothing about versions; `SKILL.md` under 500 lines with detail in
  sibling files; cross-references by current skill names.
- No internal references in skill content: no Jira, Confluence, Slack or internal-repo links,
  ticket keys, or paths users cannot obtain. No placeholder hosts such as `your-domino.com`;
  use `$DOMINO_API_HOST` or the value an API response returns.

Existing skills predate these requirements and many violate them (directory names, missing
frontmatter, stale links). Fix violations in the files you are already changing. Do not sweep
the tree in an unrelated PR; tree-wide fixes have their own tracked work.

## Commands

```bash
claude plugin validate .                              # manifest and structure
scripts/check-version.sh origin/develop               # what CI will say (use your PR's base)
scripts/verify-update-flow.sh                         # install/update behaviour (needs the claude CLI, ~2 min)
claude --plugin-dir .                                 # load this checkout in place; replaces a same-named installed plugin for the session
/reload-plugins                                       # inside a session, after editing a skill
```

Triggering test until this repo has `evals/` cases for `claude plugin eval .`: three prompts
that should load the skill and one neighbouring prompt that should not; check which activates.

## Pull requests

- Fill every section of `.github/PULL_REQUEST_TEMPLATE.md`. Under **Model attestation**,
  write the model identifier and tick neither box: the human who reviews and opens the PR
  ticks one. An agent never attests for a human.
- Base branch: `develop` for content, `main` for the promotion PR and repo mechanics.
- Merging needs the `version` check, one approving review, a code-owner review where
  `.github/CODEOWNERS` matches, and an up-to-date branch. When the base moves, rebase or use
  "Update branch".

## Things that will bite you

- Editing the marketplace clone changes nothing Claude loads until the version changes and
  `claude plugin update` runs. Editing the cache copy under `~/.claude/plugins/cache/` takes
  effect but is overwritten on update. Do neither; test with `--plugin-dir`.
- The Domino Workspace image installs this plugin from a local marketplace with auto-update
  off by default. A bump on `main` reaches laptops through the Anthropic marketplace once the
  pin advances; it reaches Workspaces only after the image turns auto-update on or runs
  `plugin update` at launch.
- `SKILL_AUDIT.md` is from May 2026 and stale; do not treat it as current.

## Domino API, SDK, and platform skills

Before you write or change Domino API, SDK, app, extension, or governance automation in this repo:

1. Read **`skills/domino-api-intro/SKILL.md`** and apply its authentication rules.
2. Open sibling files in that folder when needed:
   - **`HOSTS.md`** for base URL and gateway vs public URL
   - **`LIMITS.md`** for pagination and legacy API key guidance
   - **`ERRORS.md`** for retries and known failure patterns
   - **`SDK-MAP.md`** to pick a domain skill
   - **`API-SPECS.md`** for OpenAPI files and route discovery
3. Follow https://docs.domino.ai/cloud/reference/api/domino-api-authentication for all HTTP auth (proxy, access token, PAT, service account). Legacy user API keys are described as deprecated, never recommended.
4. For API paths and pages, use [API-SPECS.md](skills/domino-api-intro/API-SPECS.md) (public routes section) before guessing routes.
5. Then use the relevant skill under `skills/` (python-sdk, apps, domino-governance, domino-extensions, and others).

This applies even when another Domino skill is already active. The intro skill takes precedence for auth, host, and retry rules.

Product doc links in new material: full **`https://docs.domino.ai/...`** URLs only.
