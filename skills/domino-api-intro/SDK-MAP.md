# SDK and skill map

Where to go after [SKILL.md](./SKILL.md). All product doc links use https://docs.domino.ai/...

## Platform API vs other surfaces

| Surface | Typical base | Plugin skill / reference |
|---------|--------------|---------------------------|
| Control-plane REST (`/v4/...`, `/api/...`) | `DOMINO_USER_HOST` in a run; public URL outside | [python-sdk](../python-sdk/SKILL.md), [API-REFERENCE](../python-sdk/API-REFERENCE.md) |
| Jobs and scheduled runs | Same as platform | [jobs](../jobs/SKILL.md), [API-JOBS](../python-sdk/API-JOBS.md) |
| Projects, git, collaborators | Same | [projects](../projects/SKILL.md), [API-PROJECTS](../python-sdk/API-PROJECTS.md) |
| Datasets and snapshots | Same | [datasets](../datasets/SKILL.md), [API-DATASETS](../python-sdk/API-DATASETS.md) |
| Datasource audit (paginated) | Same or public URL | [data-connectivity](../data-connectivity/SKILL.md) |
| NetApp volumes admin vs WebVFS files | **Split hosts** | [netapp-volumes](../netapp-volumes/SKILL.md), [HOSTS.md](./HOSTS.md) |
| Apps publish and management | Platform + app container patterns | [apps](../apps/SKILL.md), [API-APPS](../apps/API-APPS.md) |
| Model serving and registry | Platform + inference URL from API | [domino-model-serving](../domino-model-serving/SKILL.md), [model-endpoints](../model-endpoints/SKILL.md) |
| Governance / guardrails | Often public URL when sidecar lacks route | [domino-governance](../domino-governance/SKILL.md) |
| Extensions | Platform + extension host conventions | [domino-extensions](../domino-extensions/SKILL.md) |
| Workspaces (session APIs from outside) | Public URL + PAT | [workspaces](../workspaces/SKILL.md) |
| Admin, users, orgs | Platform | [API-ADMIN](../python-sdk/API-ADMIN.md) |

## Platform API gateway (routing)

Domino can route many platform APIs through a run-local listener (port 8763). Which routes are registered depends on deployment configuration. Host and env tables: [HOSTS.md](./HOSTS.md).

## Domino AI Gateway (LLM providers)

**Not** the same as the platform API gateway. AI Gateway proxies calls to external LLM vendors (OpenAI, Bedrock, and others) with Domino-managed keys:

[ai-gateway](../ai-gateway/SKILL.md)

GenAI model products and inference vanity paths: [model-endpoints](../model-endpoints/SKILL.md).

Governance journeys: [domino-governance](../domino-governance/SKILL.md) workflow docs.

## Discovery for agents

| Resource | Purpose |
|----------|---------|
| https://docs.domino.ai/llms.txt | Short API page index |
| https://docs.domino.ai/llms-full.txt | Expanded index (primary) |
