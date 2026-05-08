# Skill Audit — Compliance with Skill Authoring Standards

Generated 2026-05-08 against the rules in
[CONTRIBUTING.md](./CONTRIBUTING.md#skill-authoring-standards).

This is a tracking checklist. No fixes are landed in the PR that introduces
this file — the audit captures the work to be done so the team can chip away
at retrofits without losing track.

## Clean skills (3)

These skills have zero violations and can be used as references when authoring
new ones:

- `skills/data-connectivity/SKILL.md`
- `skills/experiment-tracking/SKILL.md`
- `skills/netapp-volumes/SKILL.md`

## Violations by skill (18)

Each item links to the rule it violates and the offending line(s). Check the
box when fixed and the corresponding line(s) verified against the live API.

### `skills/jobs/SKILL.md` — rules 1, 2, 3, 4, 6 (highest impact)

- [ ] **Rule 1** (auth): lines 47, 70, 90 — `DOMINO_USER_API_KEY`,
      `X-Domino-Api-Key: YOUR_API_KEY`
- [ ] **Rule 2** (host): line 89 — `https://your-domino.com/v4/projects/...`
- [ ] **Rule 3** (SDK): line 43 — `from domino import Domino`
- [ ] **Rule 4** (endpoint): line 89 —
      `/v4/projects/{project_id}/runs` → `/api/jobs/v1/jobs`
- [ ] **Rule 6** (artifacts): lines 108, 193, 261, 264 —
      `/mnt/artifacts/model.pkl`, `/mnt/artifacts/model.joblib`, etc.

### `skills/python-sdk/SKILL.md` — rules 1, 2, 4

Rule 3 is **N/A** — this skill is the SDK reference. It should mark which
methods still work vs. are deprecated rather than be banned outright.

- [ ] **Rule 1** (auth): lines 69, 224, 389 — `DOMINO_USER_API_KEY`,
      `X-Domino-Api-Key: "your-api-key"`
- [ ] **Rule 2** (host): lines 61, 68, 230, 237 —
      `host="https://your-domino.com"`, etc.
- [ ] **Rule 4** (endpoint): lines 237, 252, 253 —
      `/v4/projects/{id}/runs` → `/api/jobs/v1/jobs`

### `skills/ai-gateway/SKILL.md` — rules 1, 2

- [ ] **Rule 1** (auth): lines 59, 116 —
      `headers={"X-Domino-Api-Key": "YOUR_API_KEY"}`
- [ ] **Rule 2** (host): lines 58, 80, 101, 113 —
      `https://your-domino.com/api/aigateway/v1/...`

### `skills/launchers/SKILL.md` — rules 1, 2, 6

- [ ] **Rule 1** (auth): line 236 —
      `headers={"X-Domino-Api-Key": "YOUR_API_KEY"}`
- [ ] **Rule 2** (host): line 235 —
      `https://your-domino.com/v4/launchers/...`
- [ ] **Rule 6** (artifacts): line 280 —
      `joblib.load('/mnt/artifacts/model.joblib')`

### `skills/domino-data-sdk/SKILL.md` — rules 1, 2

Rule 3 is **N/A** — this skill is the data-SDK reference.

- [ ] **Rule 1** (auth): line 176 —
      `os.environ["DOMINO_USER_API_KEY"] = "your-api-key"`
- [ ] **Rule 2** (host): line 177 —
      `os.environ["DOMINO_API_HOST"] = "https://your-domino.com"`

### `skills/domino-governance/SKILL.md` — rule 1

- [ ] **Rule 1** (auth): lines 13, 42, 63, 73, 87, 97, 102, 116, 125, 149, 157
      — `API_KEY="$DOMINO_USER_API_KEY"`, `X-Domino-Api-Key: $API_KEY`
      throughout

### `skills/datasets/SKILL.md` — rules 3, 6

- [ ] **Rule 3** (SDK): line 41 — `from domino import Domino`
- [ ] **Rule 6** (artifacts): line 272 — table row recommending
      `/mnt/artifacts/` for "Model artifacts"

### `skills/distributed-computing/SKILL.md` — rules 3, 6

- [ ] **Rule 3** (SDK): line 61 — `from domino import Domino`
- [ ] **Rule 6** (artifacts): lines 149, 152 —
      `result.write.parquet("/mnt/artifacts/output/", ...)`,
      `result.write.csv("/mnt/artifacts/output.csv", ...)`

### `skills/model-monitoring/SKILL.md` — rules 3, 6

- [ ] **Rule 3** (SDK): line 216 — `from domino import Domino`
- [ ] **Rule 6** (artifacts): lines 53, 132, 209 — training/ground-truth/model
      writes to `/mnt/artifacts/`

### `skills/projects/SKILL.md` — rules 3, 6

- [ ] **Rule 3** (SDK): line 46 — `from domino import Domino`
- [ ] **Rule 6** (artifacts): lines 176, 290 — describes `/mnt/artifacts/` as
      the home for output artifacts

### `skills/workspaces/SKILL.md` — rules 3, 6

- [ ] **Rule 3** (SDK): line 45 — `from domino import Domino`
- [ ] **Rule 6** (artifacts): line 65 — describes `/mnt/artifacts/` as
      "Project artifacts"

### `skills/environments/SKILL.md` — rule 6

- [ ] **Rule 6** (artifacts): line 71 — `ENV MODEL_PATH=/mnt/artifacts/model.pkl`

### `skills/flows/SKILL.md` — rule 6

- [ ] **Rule 6** (artifacts): line 90 —
      `{"output_path": "/mnt/artifacts/processed.parquet"}`

### `skills/genai-tracing/SKILL.md` — rule 3

- [ ] **Rule 3** (SDK): line 45 — `pip install ...dominodatalab[data,aisystems]`

### `skills/domino-ui-design/SKILL.md` — rule 1

- [ ] **Rule 1** (auth): line 92 — `return {'X-Domino-Api-Key': api_key}`

### `skills/modeling-assistant/SKILL.md` — rule 1

- [ ] **Rule 1** (auth): line 25 — `Set DOMINO_API_KEY and DOMINO_HOST
      environment variables...`

### `skills/model-endpoints/SKILL.md` — rule 2

- [ ] **Rule 2** (host): line 97 — `https://your-domino.com/models/abc123/...`

### `skills/app-deployment/SKILL.md` — rule 2

- [ ] **Rule 2** (host): line 128 —
      `https://your-domino-instance/apps-internal/APP_ID/endpoint`

## Per-rule totals

| Rule | Skills affected |
|------|-----------------|
| 1 — Auth (drop `X-Domino-Api-Key`) | 9 |
| 2 — Host env vars (drop `your-domino.com` placeholders) | 9 |
| 3 — Drop `python-domino` SDK examples | 13 (excluding 2 SDK-reference skills) |
| 4 — Verified API endpoints | 2 |
| 5 — Smoke-tested payloads | 0 found by static audit; verify per-PR |
| 6 — Storage-tier guidance | 9 |

## How to retrofit

When fixing a skill:

1. Read [CONTRIBUTING.md § Skill Authoring Standards](./CONTRIBUTING.md#skill-authoring-standards)
2. For Rule 1: replace every `X-Domino-Api-Key` example with the
   `localhost:8899/access-token` → `Authorization: Bearer $TOKEN` pattern
3. For Rule 2: substitute `$DOMINO_API_HOST` (or
   `$DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT` for remotefs) for any host placeholder
4. For Rule 3: replace SDK calls with `curl` or `requests` examples
5. For Rule 4 / 5: verify each endpoint path and payload against the current
   API docs and run a smoke-test
6. For Rule 6: replace `/mnt/artifacts/` recommendations with the right tier
   per use case
7. Re-run the relevant skill end-to-end and confirm it activates correctly
8. Tick the box(es) above and remove the skill from the list when zero
   violations remain
