# Working on domino-claude-plugin

This file is for agents and people changing **this repository**. Rules for what a skill may
tell an agent to do at runtime live in the skills themselves and in `CONTRIBUTING.md`.

## What this is

A Claude Code plugin (`.claude-plugin/plugin.json`, name `dominodatalab`) whose `skills/` are
also consumed by Codex, Copilot, OpenCode and Antigravity through `~/.agents/skills`. Content
here is installed into customer environments from a **public** repository. Two facts drive
most rules below:

1. Claude Code caches a marketplace plugin under its `plugin.json` `version` string and only
   re-reads it when that string changes. A content change without a version change ships to
   nobody.
2. The content targets **Domino 6.3 (self-managed) and Domino Cloud** from one tree. Where
   the product differs, the skill branches at runtime; we do not fork content per version.

## Layout

| Path | Contents |
|---|---|
| `skills/<name>/SKILL.md` | One skill per directory; `name` in frontmatter **must equal** the directory name. Reference files sit beside `SKILL.md`. |
| `agents/`, `commands/`, `templates/`, `output-styles/`, `hooks/` | Claude-only components |
| `mcp-servers/` | Bundled MCP server (`.mcp.json` at the root points at it) |
| `.claude-plugin/plugin.json` | Manifest. `version` is release state, not something to edit casually |
| `scripts/check-version.sh` | The CI version gate; run it locally before opening a PR |
| `scripts/verify-update-flow.sh` | Reproduces how Claude installs and updates this plugin |
| `.github/` | PR template, `version-check.yml`, `tag-release.yml`, `CODEOWNERS` |

## Branches and versions

| Branch | Role | Version rule |
|---|---|---|
| `develop` | Integration branch. **All content PRs target it.** | `plugin.json` `version` must be unchanged; CI fails a bump here |
| `main` | What ships: the Anthropic marketplace pins it, and Domino Workspaces fall back to it | Changed only by the `develop` → `main` promotion PR, which bumps once and gets a tag |
| `release-X.Y` | Snapshot for a Domino line, cut only when `main` stops being correct for it | Cherry-picks only; version stays on that line |

- Version format is `YYYY.X-Y.N`, for example `2026.6-3.1`: year, Domino line as a **floor**
  (`6-3` = 6.3 and later including Cloud), release counter. `N` never repeats and never resets.
  The tag is `release-<version>`, created by CI on merge to `main` or `release-*`.
- Never create a branch named `release-*` for anything but a real snapshot. The Domino
  Workspace updater resolves `release-X.Y.Z`, `release-X.Y`, `main` by exact name and would
  serve an integration branch to every matching cluster on its next launch.
- Repo mechanics only (`.github/`, `scripts/`, `CONTRIBUTING.md`, `README.md`, this file) may
  target `main` directly; they touch no content paths, so no bump and no tag.
- Run `scripts/check-version.sh origin/develop` (or `origin/main`) before pushing. It applies
  the same rules CI does and prints why it fails.

## Before you change skill content

**Verify against primary sources, in this order.** Skills in this repo have shipped invented
REST routes, invented YAML formats and non-existent SDK methods before; every one was
plausible and every one was wrong.

1. Published Public API specs, both targets:
   `https://docs.domino.ai/api-specs/6.3/public-api.json` and
   `https://docs.domino.ai/api-specs/cloud/public-api.json`. A route must exist in the spec
   for every Domino version the skill claims.
2. Product docs: `https://docs.domino.ai/llms.txt` indexes every page; any page is readable
   as Markdown by appending `.md`. Cloud pages live under `/cloud/`, 6.3 under `/6.3/`.
3. A deployment's own reference at `https://<domino-domain>/docs` (unauthenticated, one
   OpenAPI document per service under `/docs/openapi/`). `openapi-public.json` there is the
   deployment's full Public API. `$DOMINO_API_HOST/assets/public-api.json` is only a subset
   and omits governance, taxonomy, monitoring, NetApp and dataset-file routes.
4. `python-domino` methods: only what exists in `domino/domino.py` on the `master` branch of
   `github.com/dominodatalab/python-domino`.

**Rules that are not negotiable**

- `/v4/*` routes are the Domino **Internal API** (documented per cluster under `/docs`, absent
  from the Public API). Prefer the `/api/...` equivalent; where none exists, label the call
  "internal API, may change between Domino versions" at the point of use.
- Authentication: inside a run, `DOMINO_API_PROXY` with no header, or a bearer token from
  `http://localhost:8899/access-token`; outside a run, a Personal Access Token or service
  account token. Legacy user API keys are described as deprecated and never recommended.
- Every `SKILL.md` carries `compatibility:` frontmatter and opens its body with
  `Applies to Domino 6.3 and Domino Cloud.` A "Which path applies" section, keyed on
  `GET $DOMINO_API_HOST/version`, appears **only** where behaviour differs between the two.
  Today that is one skill: `domino-llm-access` (legacy AI Gateway on 6.3 only, removed on
  Cloud). Never tell an agent to reinstall, downgrade or repin the plugin.
- No internal references in skill content: no Jira, Confluence, Slack or internal-repo links,
  no ticket keys, no paths to scripts users cannot obtain. Cite `docs.domino.ai`, never
  `docs.dominodatalab.com/en/latest`.
- `description` is loaded for every skill on every turn: keep it to triggering language
  under 1,024 characters, with nothing about versions. `SKILL.md` stays under 500 lines;
  details go in sibling files. Cross-reference skills by their current names.
- No placeholder hosts such as `your-domino.com` presented as real values; use environment
  variables (`$DOMINO_API_HOST`) or the value an API response returns (an endpoint's `url`).

## Commands

```bash
claude plugin validate .                      # manifest and structure
scripts/check-version.sh origin/develop       # what CI will say about your version
scripts/verify-update-flow.sh                 # install/update behaviour (needs the claude CLI, ~2 min)
claude --plugin-dir .                         # load this checkout in place for a manual test
/reload-plugins                               # inside a session, after editing a skill
```

Manual triggering test until `evals/` exists: pick three prompts that should load the skill
and one neighbouring prompt that should not, and check which skill activates.

## Pull requests

- Fill every section of `.github/PULL_REQUEST_TEMPLATE.md`. Reviewers send back PRs with
  required sections unticked.
- **Model attestation is a human's statement.** If you are an agent that authored or rewrote
  skill content, write the model identifier in the PR and leave the attestation checkbox
  unticked for the human who reviews and opens it.
- Base branch: `develop` for content, `main` for the promotion PR and repo mechanics.
- Branch protection requires the `version` check, one approving review, a code-owner review
  and an up-to-date branch. When `develop` moves under your PR, rebase or use
  "Update branch".

## Things that will bite you

- Editing files under `~/.claude/plugins/cache/...` or in a marketplace clone changes nothing
  Claude loads until the version string changes and `claude plugin update` runs. Test with
  `--plugin-dir` instead.
- The Domino Workspace image installs this plugin from a local marketplace whose auto-update
  is off by default; a bump on `main` reaches laptops via the Anthropic marketplace but reaches
  Workspaces only once the image turns auto-update on or runs `plugin update` at launch.
- Keep one git operation at a time in this checkout; parallel rebases and branch creations
  collide on the index lock.
- `SKILL_AUDIT.md` is stale (May 2026) and slated for retirement; do not treat it as current.
