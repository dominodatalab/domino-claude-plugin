---
name: domino-llm-access
description: Call Large Language Models from code running in Domino and choose how the model is reached. Option A, an external provider (OpenAI, Anthropic, AWS Bedrock, Azure OpenAI, Google Vertex AI) with the API key stored as a Domino environment variable. Option B, a Domino-hosted model endpoint (vLLM, OpenAI-compatible) created from a Hugging Face model or a registered model, called with the OpenAI SDK or Pydantic AI using the in-run access token. Covers the Host an LLM UI and REST API (/api/gen-ai/beta), endpoint monitoring, LLM Gateway 2.0 on Domino Cloud, and the legacy AI Gateway on Domino 6.3. Use when a user asks how to call an LLM from a Workspace, Job, App or agent, where to put an LLM API key, how to get an endpoint base_url or token, how to host, deploy or serve an LLM with vLLM, how to use or migrate off the AI Gateway, or what LLM Gateway 2.0 is.
compatibility: Domino 6.3 and Domino Cloud. Requires DOMINO_API_HOST; in a run use DOMINO_API_PROXY or the localhost:8899 access-token endpoint, outside a run a Personal Access Token. The legacy AI Gateway section applies to Domino 6.3 only, and only where an administrator has enabled it.
---

# LLM access in Domino

Applies to Domino 6.3 and Domino Cloud. One section differs between them; see "Which path applies" first.

## Which path applies

Domino offers two ways to reach a model, on both targets:

- **Option A: external provider.** Your code calls OpenAI, Anthropic, Bedrock, Azure OpenAI or Vertex AI directly through the provider's SDK. Domino runs the code and injects the API key as an environment variable.
- **Option B: Domino-hosted endpoint.** Domino serves a model you registered (from Hugging Face or an experiment run) with vLLM on a GPU hardware tier and exposes an OpenAI-compatible API.

A centralized gateway in front of external providers is the part that depends on the deployment:

| Deployment | Gateway situation | What to tell the user |
|---|---|---|
| **Domino Cloud** | The legacy AI Gateway has been **removed**: no Gateway LLMs UI, no `/api/aigateway/*` routes, no gateway audit trail. Code using the MLflow Deployment Client against a gateway endpoint fails. The successor is **LLM Gateway 2.0**, distributed today as a binary deployed as a Domino App, on request from the Domino field team. | Use Option A or B. Mention LLM Gateway 2.0 only if they need usage tracking, cost controls or guardrails across teams. See "Migrate off the legacy AI Gateway" if they have old gateway code. |
| **Domino 6.3** | The legacy AI Gateway exists but is **not enabled by default**; it works only where an administrator explicitly enabled it. LLM Gateway 2.0 is available on request, as on Cloud. | Use Option A or B. If the deployment has the gateway enabled and the user already has endpoints there, see [LEGACY-AI-GATEWAY.md](./LEGACY-AI-GATEWAY.md). |

To find out which deployment you are on, read the version: `GET $DOMINO_API_HOST/version` returns JSON with a `version` field (this is the endpoint the `python-domino` SDK uses). A `6.3.x` value is self-managed 6.3; Cloud reports a later build. On 6.3, whether the legacy gateway is enabled is a deployment setting; a `GET $DOMINO_API_HOST/api/aigateway/v1/endpoints` that returns 404 or an error means it is not available, and you should not try to enable it or work around that. If the version is below 6.3, this skill does not cover the deployment; say so and point the user to docs.dominodatalab.com for their version. Never tell the user to reinstall or change the plugin.

## Decide between Option A and Option B

| | Option A: external provider | Option B: host in Domino |
|---|---|---|
| Where inference runs | At the provider, outside Domino | On Domino compute, on a GPU tier you choose |
| Who manages the model | The provider | You, through a Domino endpoint |
| Choose it when | You want a frontier model and may send prompts outside the cluster | External providers are not permitted, you need data residency or cost control, or you fine-tuned the model yourself |
| You configure | The provider's SDK and an API key | Model registration, endpoint, GPU hardware tier, scaling |

Both are first-class. Domino-hosted endpoints are OpenAI-compatible, so code written against an OpenAI-style client can move between the two later by changing `base_url` and the key, not the call.

Many production systems use both: an external frontier model for primary reasoning and a Domino-hosted model for a specialized task such as a fine-tuned classifier or an embedding model. If the user is building an agent, the `@add_tracing` instrumentation in the `domino-genai-tracing` skill captures traces from every LLM call regardless of where the model runs.

## Option A: call an external provider

1. **Install the provider's SDK** in the Compute Environment (add `RUN pip install openai`, `anthropic`, `boto3`, or `google-cloud-aiplatform` to the Dockerfile instructions) or install it in the Workspace.
2. **Store the API key as a Domino environment variable** in the Project's settings. Domino injects Project environment variables into Workspaces and Jobs, so the key stays out of code and version control.
3. **Read the key with `os.environ` and call the SDK as you would anywhere.** Nothing about the call is Domino-specific.

| Provider | SDK / package | Environment variable(s) |
|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` |
| AWS Bedrock | `boto3` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| Azure OpenAI | `openai` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` |
| Google Vertex AI | `google-cloud-aiplatform` | Service account credentials |

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
response = client.chat.completions.create(
    model="gpt-5.4-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

With Pydantic AI, as in Domino's documentation:

```python
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    "gpt-5.4-mini",
    provider=OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"]),
)
agent = Agent(model)
print(agent.run_sync("Hello").output)
```

Do not hard-code keys, do not commit them, and do not suggest passing them on the command line. If the user's organization forbids sending prompts to third parties, go to Option B.

## Option B: host a model in Domino

Requires **Project Collaborator** permission to register models and create endpoints, and a **GPU hardware tier**: CPU tiers do not give acceptable latency, and the tier's GPU memory must hold the model's weights (a 7B-parameter model needs at least about 16 GB of VRAM; 13B and larger, at least 24 GB). Start with a tier that meets the requirement and scale after observing the Performance tab.

### Step 1: register a model

Go to **Models** > **Register**. Choose the source: a **Hugging Face** model the user has access to (some models require accepting a license on Hugging Face first), or an **experiment run** that logged an MLflow model. Complete the required fields.

### Step 2: create an endpoint

From the registered model's **Endpoints** tab, click **Create endpoint**:

1. Complete the endpoint configuration details.
2. Under **Environment**, select **Domino vLLM Environment**. It is pre-configured with the vLLM runtime, which provides optimized inference and the OpenAI-compatible API.
3. Under **Hardware Tier**, select a GPU-enabled tier sized for the model.
4. Configure access by adding users or organizations.
5. Some models need extra vLLM arguments to work with agent frameworks' tool calling. Under **Configuration** > **Advanced** > **vLLM arguments** add `--enable-auto-tool-choice` and `--tool-call-parser hermes`.
6. Click **Create endpoint**.

To do the same through the REST API (`/api/gen-ai/beta/endpoints`, identical on 6.3 and Cloud), see [HOST-AN-LLM-API.md](./HOST-AN-LLM-API.md).

### Step 3: call the endpoint

Once the endpoint is **Running**, open its **Calling** tab. It shows the endpoint URL, which is the `base_url` for an OpenAI-style client, and a ready-made OpenAI SDK snippet. Inside a Workspace, Job or App, the bearer token is available from the local sidecar:

```python
import os
import requests
from openai import OpenAI

ENDPOINT_URL = os.environ["DOMINO_LLM_ENDPOINT_URL"]           # copied from the Calling tab
API_KEY = requests.get("http://localhost:8899/access-token").text  # in-run access token

client = OpenAI(base_url=ENDPOINT_URL, api_key=API_KEY)
response = client.chat.completions.create(
    model="your-model-name",   # the servedModelName shown on the endpoint
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

The OpenAI Responses API is also supported by the endpoint. With Pydantic AI, pass `OpenAIProvider(base_url=ENDPOINT_URL, api_key=API_KEY)` to `OpenAIChatModel("your-model-name", ...)` exactly as in Option A.

Store the URL as a Domino environment variable such as `DOMINO_LLM_ENDPOINT_URL` rather than hard-coding it, so promoting from a development endpoint to a production one is a configuration change. The token from `localhost:8899` is short-lived and only exists inside a Domino execution; code running outside Domino (a laptop, external CI) uses a Personal Access Token as the bearer instead.

### Step 4: monitor

The endpoint detail page has **Overview** (configuration and deployment status), **Performance** (token usage and latency over time) and **Usage** (invocation frequency). The same numbers are available from the REST metrics routes in [HOST-AN-LLM-API.md](./HOST-AN-LLM-API.md).

### Troubleshooting

| Problem | What to check |
|---|---|
| Hugging Face model not listed | The user must have access to the model; some require accepting a license agreement on Hugging Face first. |
| Endpoint stuck in **Starting** | Model size versus the tier's GPU memory. Read the endpoint logs for the specific error. |
| Slow responses or timeouts | Performance tab for latency patterns; if concurrent requests exceed capacity, use a larger tier or a second endpoint. |
| Users cannot access the endpoint | They or their organization must be in the endpoint's access controls and hold the required Project permissions. |
| Tool calls fail from an agent framework | Add `--enable-auto-tool-choice --tool-call-parser hermes` to the vLLM arguments (Step 2). |

## Gateways

### LLM Gateway 2.0 (Cloud and 6.3, on request)

LLM Gateway 2.0 is the successor to the legacy AI Gateway. It centralizes external-provider access and adds usage tracking across users, Projects and models; cost controls including per-team and per-model budgets; guardrails for prompt and response inspection; and broader model and vendor coverage. Domino distributes it today as a binary deployed as a Domino App and plans native integration in a future release. It is obtained from the user's Domino field representative; there is no self-service install and no public API to document here. Do not invent configuration for it.

### Legacy AI Gateway (6.3 only, where enabled)

Off by default in 6.3 and removed from Cloud. If the deployment has it enabled, [LEGACY-AI-GATEWAY.md](./LEGACY-AI-GATEWAY.md) covers the Gateway LLMs UI, the MLflow Deployment Client calls it supports, its `/api/aigateway/v1` routes with verified request bodies, permissions and the audit download.

### Migrate off the legacy AI Gateway

1. **Find the code.** Search the Project for `mlflow.deployments.get_deploy_client(...)` and for `predict()`, `get_endpoint()` or `list_endpoints()` against a Domino AI Gateway target, and for any `/api/aigateway/` URL. All of it fails on Cloud and on a 6.3 deployment where the gateway is disabled.
2. **Pick the replacement.** LLM Gateway 2.0 if the team needs centralized tracking, budgets or guardrails; otherwise Option A (provider SDK) or Option B (Domino-hosted endpoint).
3. **Move the credentials.** Provider keys that the gateway held in Domino's central vault are no longer reachable through it. Store them as Project environment variables (or as inputs to the LLM Gateway 2.0 configuration) and read them with `os.environ`.
4. **Update the calls and rerun** the affected Jobs, Apps and agents end to end.

## Verify before you write API calls

Confirm routes and fields against the deployment's own API reference before generating code: `https://<domino-domain>/docs` (unauthenticated) renders one OpenAPI document per service, and `/docs/openapi/openapi-public.json` is the deployment's complete Public API. `$DOMINO_API_HOST/assets/public-api.json` is a smaller subset that does include the `/api/gen-ai/beta` routes used here. The published specs this skill was written against are `https://docs.domino.ai/api-specs/6.3/public-api.json` and `https://docs.domino.ai/api-specs/cloud/public-api.json`; every route in the two reference files exists in the spec named on it.

## Documentation

- Set up LLM access: https://docs.domino.ai/cloud/platform-capabilities/features/llms (6.3: replace `cloud` with `6.3`)
- Host an LLM: https://docs.domino.ai/cloud/platform-capabilities/features/llms/host-an-llm
- LLM Gateway 2.0 and migration: https://docs.domino.ai/cloud/platform-capabilities/features/llms/llm-gateway
- Legacy AI Gateway (6.3): https://docs.domino.ai/6.3/platform-capabilities/features/llms/ai-gateway and https://docs.domino.ai/6.3/admin/platform-configuration/ai-gateway
- Develop agentic systems (tracing): https://docs.domino.ai/cloud/platform-capabilities/features/agents/develop
