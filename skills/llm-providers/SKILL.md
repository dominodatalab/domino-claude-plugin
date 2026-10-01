---
name: domino-llm-providers
description: Build multi-provider LLM client code that runs against local Domino-hosted vLLM endpoints, the Anthropic API directly, and AWS Bedrock via the Domino AI Gateway — all from the same agent codebase. Covers model rosters, per-provider quirks, token refresh for sidecar-authenticated endpoints, the Qwen thinking flag, and streaming patterns that capture token usage across all providers. Use when building Domino agents that need to swap LLM providers at runtime, demo model comparisons, or run local + frontier models side-by-side.
---

# Domino LLM Providers Skill

Patterns for calling **multiple LLM providers from one Python agent codebase**:
local Domino-hosted vLLM endpoints, Anthropic Claude API direct, and AWS
Bedrock via the Domino AI Gateway. The OpenAI Python SDK is the common
client surface; what changes per provider is base URL, auth, and a few
request-body knobs.

## When to use this skill

Use this skill when you are:
- Building an agent that lets the user pick between local and frontier models
- Adding a new LLM provider (Anthropic, Bedrock, etc.) to existing agent code
- Hitting `400` errors on extra-body params or `401` errors on token refresh
- Trying to capture token usage on streamed responses across providers
- Running model-comparison demos where the same query hits 3+ providers

## When this is NOT the right skill

- **Setting up tracing / span waterfalls / evaluators** → use `domino-genai-tracing`.
  This skill is about *making the call*; that one is about *observing it*.
- **Creating Gateway endpoints, managing API keys, or controlling access** →
  use `domino-ai-gateway`. That skill is administrative; this one is
  developer-focused (the application code that consumes Gateway endpoints).

## Provider matrix at a glance

| Provider | Base URL pattern | Auth | Notes |
|----------|------------------|------|-------|
| Domino vLLM (local) | `https://<host>/endpoints/<endpoint>/v1` | Bearer from sidecar token service | Token expires; refresh per call. `served_model_name` is often `.` for vLLM endpoints |
| Anthropic direct | `https://api.anthropic.com/v1/` | `ANTHROPIC_API_KEY` env | Claude models via OpenAI-compat layer — no `anthropic` SDK needed |
| Bedrock via Domino AI Gateway | `$AWS_BEDROCK_BASE_URL` | `$AWS_BEDROCK_API_KEY` | OpenAI-compatible; access controlled by Gateway endpoint, not direct AWS |

All three use the same `OpenAI()` Python client class — only base URL,
api_key, and request-body extras change per provider.

## The 30-second pattern

```python
from openai import OpenAI

# Same client class for every provider; only base_url + api_key change
client = OpenAI(
    base_url="https://api.anthropic.com/v1/",  # or Domino vLLM URL, or Gateway URL
    api_key=api_key,
    timeout=90.0,
    max_retries=1,
)

response = client.chat.completions.create(
    model=served_model_name,           # "claude-sonnet-4-6", ".", "deepseek.v3.2", ...
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=1024,
    extra_body={},                     # Provider-specific knobs (see LOCAL-VLLM.md)
)
```

The complexity hides in three places:
1. **Resolving** which (base_url, api_key, model_id, extras) tuple to use → see `MODEL-ROSTER.md`
2. **Refreshing** auth for Domino vLLM endpoints → see `LOCAL-VLLM.md`
3. **Capturing** token usage on streamed responses → see `STREAMING.md`

## Documentation in this skill

- **[MODEL-ROSTER.md](./MODEL-ROSTER.md)** — Config-driven multi-provider routing.
  YAML roster format, `_resolve_model()`, `_get_llm_client()`, the runtime
  selection pattern that lets users swap providers via the UI.
- **[LOCAL-VLLM.md](./LOCAL-VLLM.md)** — Local Domino-hosted vLLM gotchas:
  token refresh via sidecar service, Qwen `enable_thinking` flag, vLLM's
  `served_model_name="."` quirk, base URL env-var pattern, common errors.
- **[CLAUDE-API.md](./CLAUDE-API.md)** — Anthropic Claude direct via the
  OpenAI-compat layer. Why this is preferable to the `anthropic` SDK in a
  multi-provider codebase, model ID conventions, and tracing notes.
- **[BEDROCK-VIA-AI-GATEWAY.md](./BEDROCK-VIA-AI-GATEWAY.md)** — Application-code
  patterns for calling Bedrock through Domino AI Gateway. Includes the
  catalog of common open-weight models on Bedrock + how to add a new one
  to your roster.
- **[STREAMING.md](./STREAMING.md)** — `stream_options={"include_usage": True}`
  to populate `mlflow.chat.tokenUsage` across providers; token usage
  parsing patterns for non-streamed responses.

## Why one client, multiple providers

Three reasons:

1. **Less code surface.** Each provider's native SDK has its own request /
   response shape. A multi-SDK codebase needs translation layers everywhere
   tokens, prompts, or tools are touched. The OpenAI client speaks the same
   shape regardless of who's behind the URL.

2. **Tracing works the same way.** `mlflow.openai.autolog()` wraps the OpenAI
   client class — every provider routed through it gets identical span
   shapes in the GenAI Eval Dashboard, comparable across providers.

3. **Demo audience cares about model differences, not SDK differences.** A
   credit-sales rep doesn't care that Claude has a `messages` API and
   OpenAI has a `chat/completions` API. They care about latency, quality,
   and cost — surfaces the framework abstracts away.

## Reference implementation

The Pierpoint Credit Sales demo (`fsi-demo` on the platform) ships a
working multi-provider chatbot with all three provider types in one
roster. Key files:
- `app/agent_config.yaml` — roster definition
- `app/api/chatbot.py` — `_get_llm_client()`, `_call_llm_with_retry()`,
  `_call_llm_streaming()`

Each documentation page in this skill links to the relevant section of
that codebase as a working example.
