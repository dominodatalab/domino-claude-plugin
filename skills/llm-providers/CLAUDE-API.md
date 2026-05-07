# Anthropic Claude API — Direct Integration via OpenAI-Compat Layer

You can call Anthropic Claude models from a Domino agent without the
`anthropic` Python SDK. Anthropic publishes an **OpenAI-compatible API
layer** at `https://api.anthropic.com/v1/` that the standard `openai`
client speaks unmodified. In a multi-provider codebase this is the
cleanest path: same client class, same call shape, same tracing surface.

## When to use this versus the `anthropic` SDK

Use the OpenAI-compat layer when:
- Your codebase already calls other providers via the `openai` client
  (vLLM, Bedrock, Azure, OpenAI itself)
- You want a single tracing setup (`mlflow.openai.autolog()`) to capture
  every provider with identical span shapes
- You're not using Anthropic-specific features that aren't on the
  compat layer yet (extended thinking budgets, computer-use tool, etc.)

Use the native `anthropic` SDK when:
- You need Anthropic-only features (extended thinking with `budget_tokens`,
  Files API, computer-use, prompt caching beta, batch API)
- The codebase is single-provider Anthropic and SDK-specific helpers
  are worth more than uniformity

For most credit-sales / customer-service / sales-assistant style demos,
the compat layer is the right choice.

## Roster entry

```yaml
- key: claude-sonnet-4-6
  label: "Claude Sonnet 4.6"
  provider: anthropic
  base_url_default: "https://api.anthropic.com/v1/"
  api_key_env: ANTHROPIC_API_KEY
  context_window: 200000
```

The `api_key_env` defaults to `ANTHROPIC_API_KEY` in our reference
implementation; override per-entry if you store the key under a
different name.

## Building the client

```python
import os
from openai import OpenAI

def get_anthropic_client():
    """OpenAI client routed at Anthropic's compat layer."""
    return OpenAI(
        base_url="https://api.anthropic.com/v1/",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        timeout=90.0,
        max_retries=1,
    )
```

That's the whole integration. No `from anthropic import Anthropic`,
no `messages.create()`, no Anthropic-specific stop-sequence handling.

## Calling a Claude model

```python
client = get_anthropic_client()

completion = client.chat.completions.create(
    model="claude-sonnet-4-6",                   # Anthropic's own ID, NOT a friendly name
    messages=[
        {"role": "system", "content": "You are a credit sales assistant."},
        {"role": "user", "content": "What's the best bond on our axes today?"},
    ],
    max_tokens=1024,
    temperature=0.2,
)

print(completion.choices[0].message.content)
```

Model IDs on the compat layer use Anthropic's own naming
(`claude-sonnet-4-6`, `claude-opus-4-7`, etc.) — verify against
[Anthropic's model list](https://docs.anthropic.com/en/docs/about-claude/models)
when adding new entries.

## Streaming

Same pattern as any other OpenAI-compatible provider:

```python
stream = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[...],
    max_tokens=1024,
    stream=True,
    stream_options={"include_usage": True},
)

for chunk in stream:
    if not chunk.choices:
        # Terminal chunk with usage block — autolog captures it
        continue
    delta = chunk.choices[0].delta
    if delta and delta.content:
        print(delta.content, end="", flush=True)
```

Anthropic honours `stream_options.include_usage` on the compat layer
— the terminal chunk includes prompt/completion token counts that
`mlflow.openai.autolog()` reads into `mlflow.chat.tokenUsage`. Same
trace shape as if you'd called OpenAI or a local vLLM endpoint.

## Tracing setup

Tracing is identical to other OpenAI-compatible providers because the
client class is the same:

```python
import mlflow
mlflow.openai.autolog()  # Wraps the client class — covers ALL OpenAI() calls

# Or, scoped to your traced function:
from domino.agents.tracing import add_tracing

@add_tracing(name="my_agent", autolog_frameworks=["openai"])
def ask_claude(prompt: str) -> str:
    client = get_anthropic_client()
    return client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    ).choices[0].message.content
```

You do **not** need `mlflow.anthropic.autolog()` — that wraps the native
`anthropic` SDK's `Anthropic()` client, which you aren't using here.

## Where this works in the credit-sales demo

The Pierpoint chatbot lets the user pick `Claude Sonnet 4.6` from the
model dropdown. The runtime resolves that to:
```python
provider = "anthropic"
base_url = "https://api.anthropic.com/v1/"
api_key = os.environ["ANTHROPIC_API_KEY"]
served_name = "claude-sonnet-4-6"
```
and the same `_call_llm_with_retry()` code path that handles vLLM and
Bedrock executes. Tool selection, response generation, and streaming
all work identically.

## Common errors

| Error | Likely cause |
|-------|--------------|
| `401 invalid x-api-key` | `ANTHROPIC_API_KEY` not set or empty in the env |
| `404 model X not found` | Using a friendly name (`"sonnet"`) instead of full ID (`"claude-sonnet-4-6"`) |
| `400 max_tokens is required` | Anthropic requires `max_tokens` always (OpenAI defaults it; Anthropic doesn't) |
| `400 system message must come first` | Multi-system-message arrays — Anthropic accepts at most one, must be the first message |
| `529 Overloaded` | Anthropic's load shedding signal. Retry with backoff, or surface a "try again" message |

## API key management

For production, **don't** ship the key in code. Use:
- Domino **Environment Variables** (Project Settings → Environment Variables)
  for a project-scoped secret
- Domino **AI Gateway** with an Anthropic-provider endpoint if you want
  centralised key management, audit logging, and access controls
  — see the `domino-ai-gateway` skill for the admin setup, and treat
  the gateway endpoint as if it were "just another OpenAI-compatible
  base URL" in your roster

For demos, putting the key in a Domino env var is fine and is what the
credit-sales project does.

## Reference

`app/agent_config.yaml` (the `claude-sonnet-4-6` roster entry) and
`app/api/chatbot.py:1307` (the `provider == "anthropic"` branch in
`_get_llm_client()`).
