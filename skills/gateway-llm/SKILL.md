---
name: domino-gateway-llm
description: Call LLMs hosted behind a Domino AI Gateway from workspace, job, or app code using the OpenAI-compatible endpoint and the local Domino access token (http://localhost:8899/access-token). Works with the openai SDK, pydantic-ai, LangChain, or plain HTTP. IMPORTANT — the AI Gateway is an OPTIONAL platform extension and is NOT available in every Domino deployment. Only use this skill when the user EXPLICITLY asks to use the Gateway / Gateway LLMs / a gateway model. Do not assume the Gateway exists, and do not route LLM calls through it unless asked.
---

# Domino Gateway LLM Skill

How to **call** an LLM that is served through a Domino **AI Gateway** from
code running inside Domino (workspaces, jobs, scheduled runs, or deployed
apps). This skill is about *consuming* gateway models at runtime, using the
OpenAI-compatible interface and the local Domino access token.

> For configuring/creating gateway endpoints, access control, and admin-side
> usage monitoring, see the companion **domino-ai-gateway** skill.

## ⚠️ When to use this skill — read first

The AI Gateway is an **optional extension** of the Domino platform. It is
**not present in every deployment / domain**. Treat it as opt-in:

- **Only activate this skill when the user explicitly asks** for it — e.g.
  "use the gateway", "use a Gateway LLM", "route this through the AI
  Gateway", "call deepseek/mistral/claude via the gateway".
- **Do not assume the gateway exists.** If the user hasn't mentioned it,
  prefer whatever LLM access the project already uses (a deployed model
  endpoint, a direct provider SDK, a local model, etc.).
- **Verify availability before relying on it.** A `404`/"Application not
  running" on the gateway base URL means the gateway isn't deployed in this
  domain — say so plainly instead of retrying.
- The gateway **base URL is deployment-specific** (it's published as a
  Domino App). There is no universal URL — discover it or ask the user
  (see *Finding the gateway base URL*).

## What the AI Gateway gives you

A single OpenAI-compatible proxy in front of many upstream providers
(AWS Bedrock, Anthropic, Azure OpenAI, OpenAI, …) with:

- **Centralized API keys** — upstream keys live in Domino, never in your code.
- **One auth mechanism** — your existing Domino access token.
- **Governance** — centralized usage, cost, and audit logging.
- **Model aliases** — friendly names (e.g. `deepseek.v3.2`) defined in the
  Model Catalog that map to a concrete upstream model.

## Authentication — the local access token

Inside any Domino workload there is a local token broker at
`http://localhost:8899/access-token`. Fetch a token from it and pass it as
the OpenAI `api_key`. No provider key is needed in your code.

```python
import urllib.request

def domino_access_token() -> str:
    return urllib.request.urlopen(
        "http://localhost:8899/access-token"
    ).read().decode().strip()
```

> **Tokens expire.** Fetch a fresh token per call (or per short-lived client)
> rather than caching one for the life of a long-running app. The fetch is a
> localhost round-trip (~1 ms), so re-fetching is cheap and avoids
> mid-session auth redirects.

## The base URL

The gateway is exposed as a Domino App, so its base URL looks like:

```
https://<DOMINO_HOST>/apps/<GATEWAY_APP_NAME>/v1
```

The path **ends in `/v1`** (OpenAI convention). Build it once and reuse:

```python
import os

GATEWAY_BASE_URL = "https://<DOMINO_HOST>/apps/<GATEWAY_APP_NAME>/v1"
# Often the host is available as an env var:
#   os.environ.get("DOMINO_API_HOST") or os.environ.get("DOMINO_HOST")
```

## Discover available models

Don't hard-code a model name blindly — list what the gateway actually
serves. Model ids must match an **alias** exactly (a wrong name returns
`404 model not found`).

```python
import requests

token = domino_access_token()
r = requests.get(
    f"{GATEWAY_BASE_URL}/models",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)
r.raise_for_status()
for m in r.json().get("data", []):
    print(m["id"], "·", m.get("owned_by"))
```

You can also see the aliases (and their upstream provider/model + cost) in
the Domino UI under **Endpoints → Gateway LLMs → Model Catalog**.

## Call it — OpenAI SDK (recommended)

The gateway is OpenAI-compatible, so the standard `openai` client works.
Pass the **alias id** as `model`.

```python
from openai import OpenAI

client = OpenAI(base_url=GATEWAY_BASE_URL, api_key=domino_access_token())

resp = client.chat.completions.create(
    model="deepseek.v3.2",          # an alias from /v1/models
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.2,
    max_tokens=512,
)
print(resp.choices[0].message.content)
```

Tool calling, JSON mode, and the other chat-completions parameters work as
usual; whether a given parameter is honored depends on the upstream model.

## Call it — pydantic-ai

```python
import urllib.request
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

token = urllib.request.urlopen("http://localhost:8899/access-token").read().decode().strip()

model = OpenAIChatModel(
    "deepseek.v3.2",
    provider=OpenAIProvider(base_url=GATEWAY_BASE_URL, api_key=token),
)
agent = Agent(model)
print(agent.run_sync("Hello!").output)
```

## Call it — LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek.v3.2",
    base_url=GATEWAY_BASE_URL,
    api_key=domino_access_token(),
)
print(llm.invoke("What is machine learning?").content)
```

## Call it — plain HTTP

```python
import requests

resp = requests.post(
    f"{GATEWAY_BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {domino_access_token()}"},
    json={
        "model": "deepseek.v3.2",
        "messages": [{"role": "user", "content": "Hello!"}],
    },
    timeout=60,
)
resp.raise_for_status()
print(resp.json()["choices"][0]["message"]["content"])
```

## Streaming

```python
stream = client.chat.completions.create(
    model="deepseek.v3.2",
    messages=[{"role": "user", "content": "Write a haiku about the Alps"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Tracing gateway calls

Because calls go through the OpenAI SDK, MLflow OpenAI autolog and the
Domino GenAI tracing tooling capture them with no extra work — token usage,
latency, and cost land on the span. See the **domino-genai-tracing** skill.

```python
import mlflow
mlflow.openai.autolog()   # gateway chat.completions calls now produce spans
```

## A reusable wrapper

```python
import urllib.request
from openai import OpenAI

GATEWAY_BASE_URL = "https://<DOMINO_HOST>/apps/<GATEWAY_APP_NAME>/v1"

def gateway_chat(messages, model="deepseek.v3.2", **kw):
    """One-shot client with a fresh token (tokens expire on long-lived apps)."""
    token = urllib.request.urlopen(
        "http://localhost:8899/access-token"
    ).read().decode().strip()
    client = OpenAI(base_url=GATEWAY_BASE_URL, api_key=token, timeout=120)
    resp = client.chat.completions.create(model=model, messages=messages, **kw)
    return resp.choices[0].message.content
```

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `404` or HTML "Application not running" on the base URL | The gateway **isn't deployed in this domain**, or the app name/path is wrong. Confirm the gateway exists before using it. |
| `401 Unauthorized` / response is an HTML login page | Token missing or expired. Re-fetch from `localhost:8899/access-token` immediately before the call. |
| `404 model '<x>' not found` | The model id isn't a valid alias. List aliases via `GET /v1/models` or the Model Catalog and use an exact match. |
| `429 Too Many Requests` | Upstream/gateway rate limit. Back off and retry; ask an admin to raise limits. |
| Works in a workspace but not in a deployed app | Check the app can reach `localhost:8899` and the base URL; re-fetch the token per request rather than caching it. |

## Finding the gateway base URL

The base URL is deployment-specific. To find it:

1. **Ask the user** for the gateway app URL if they haven't given it.
2. In the Domino UI: **Endpoints → Gateway LLMs** (the Model Catalog lists
   aliases; the gateway app's URL is its published App URL, ending `/v1`).
3. Validate a candidate URL with `GET {base}/v1/models` using a token — a
   JSON model list confirms it; a 404/HTML page means it's wrong or absent.

## Documentation reference

- [AI Gateway](https://docs.dominodatalab.com/en/latest/user_guide/c9ac47/ai-gateway/)
- [Monitor AI Gateway LLM logs](https://docs.dominodatalab.com/en/cloud/admin_guide/984c09/monitor-ai-gateway-large-language-model-llm-logs/)
