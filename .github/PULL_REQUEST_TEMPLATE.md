### Summary of what changed and why

<!-- One paragraph. Say which skills, agents, commands, templates or distribution files
     change and what a user gets that they did not have before. -->

<!-- Maintainers link the Jira ticket (skills work lives under the DOCS-6840 epic; platform-side
     work uses DOM-). External contributors link a GitHub issue instead. List more than one,
     comma-separated, if the PR legitimately closes several. -->
**Linked ticket or issue:** DOCS-NNNN / #NNN

### Change type

Select all that apply:

- [ ] New skill (`skills/<name>/SKILL.md`)
- [ ] Fix or extension to an existing skill
- [ ] Agent, command, template, output style or hook
- [ ] MCP server
- [ ] Distribution or release mechanics (`plugin.json`, `.mcp.json`, CI, installer)
- [ ] Repo docs only (README, CONTRIBUTING, this template)

### Domino version applicability  *(required)*

<!-- The plugin targets Domino 6.3 (self-managed) and Domino Cloud. `main` must be correct
     for both. See CONTRIBUTING.md standard 7, "Declare which Domino versions a skill applies to". -->

This change applies to:

- [ ] Domino 6.3 and Domino Cloud (the default; no version-specific behaviour)
- [ ] Domino Cloud only — explain why below and gate the content
- [ ] Domino 6.3 only — explain why below and gate the content

Verified against the public API spec for **both** targets where the change cites API routes:

- [ ] `https://docs.domino.ai/api-specs/6.3/public-api.json`
- [ ] `https://docs.domino.ai/api-specs/cloud/public-api.json`
- [ ] No API routes are cited in this change

Every new or modified `SKILL.md`:

- [ ] carries `compatibility:` frontmatter naming the Domino versions it applies to
- [ ] opens its body with the scope line (`Applies to Domino 6.3 and Domino Cloud.` or the gated variant)
- [ ] if behaviour differs between 6.3 and Cloud, includes a "Which path applies" section using `GET $DOMINO_API_HOST/version`

Version notes (why a target is excluded, which routes differ, anything the reviewer must know):

N/A

### Model attestation  *(required for new or rewritten skill content)*

<!-- Skill content is instructions for an agent. It is only as good as the model that
     wrote and checked it. New skills and substantive rewrites must be authored with a
     Fable-class or Astra-class model. Drafting with a weaker model and "cleaning up"
     does not qualify. Editing a few lines of an existing skill does not require this. -->

**Model(s) used to author the skill content in this PR:** `provider/model-id` <!-- e.g. claude-fable-5-1 -->

- [ ] I attest that all new or rewritten skill content in this PR was authored using a Fable-class or Astra-class model, and that I, a human, reviewed the result before opening this PR.
- [ ] Not applicable: this PR contains no new or rewritten skill content.

### Verification checklist

Content accuracy:

- [ ] Every REST path exists in the public spec for the targets claimed above. Routes not in the spec (for example `/v4/*`) are either removed or labelled **undocumented, unsupported, may change without notice** at the point of use.
- [ ] Every `python-domino` method cited exists in [`domino/domino.py`](https://github.com/dominodatalab/python-domino/blob/master/domino/domino.py) on `master`.
- [ ] Every configuration format shown (YAML, JSON, Dockerfile) is one Domino actually accepts, with a docs.domino.ai citation.
- [ ] Authentication follows CONTRIBUTING.md standard 1: `DOMINO_API_PROXY` or the `localhost:8899` access-token endpoint in a run; Personal Access Token or service account outside a run; legacy user API keys described as deprecated, never recommended.
- [ ] Doc links point at `docs.domino.ai` (not `docs.dominodatalab.com/en/latest`).

Public-repo hygiene (this repository is public):

- [ ] No links to Jira, Confluence, Slack or internal repositories, and no internal artefacts (ticket keys, "rank N", internal script paths) in skill content.
- [ ] No placeholder hosts like `your-domino.com` presented as real values; use `$DOMINO_API_HOST` or a clearly marked placeholder.
- [ ] No credentials, tokens or customer identifiers.

Skill format:

- [ ] `name` in frontmatter equals the directory name; `description` ≤ 1,024 characters and states when to trigger; `SKILL.md` ≤ 500 lines with details in sibling files.
- [ ] Cross-references to other skills use their current names (`domino-apps`, not `domino-app-deployment`).
- [ ] A skill directory always contains `SKILL.md`; reference files alone are not a skill.

Release mechanics:

- [ ] `plugin.json` `version` is bumped to the next `YYYY.X-Y.N` (any change under `skills/`, `commands/`, `agents/`, `templates/`, `mcp-servers/`, `output-styles/` or `.mcp.json` requires it, or nothing ships to installed copies; `N` never reused; when the base branch is `release-X.Y`, the version's `X.Y` must equal it). CI enforces this.
- [ ] README skill table and counts updated for any added, renamed or removed component.
- [ ] Eval case added or updated under `evals/` for the skill(s) touched (once the eval framework exists; until then, describe the manual test below).

### Testing

<!-- What you ran and what you saw. For API payloads, which deployment version you tested
     against. For triggering, which prompts activated the skill and which did not. -->

N/A

### Branching and release

- [ ] Base branch is `main`.
- [ ] This fix must also reach a `release-X.Y` branch (once one exists): note it here so a maintainer cherry-picks after merge (backport PRs target that branch and bump `N` on its line).

### Notes for reviewers

- At least one maintainer review is required and all checks must pass before merge.
- Reviewers: spot-check at least two cited routes against the spec and one cited SDK method against `domino.py`. Reject unverified `/v4` routes and any internal reference.
