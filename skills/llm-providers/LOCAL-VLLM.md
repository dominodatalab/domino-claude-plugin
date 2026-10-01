# Local LLM (Domino-hosted vLLM) — Gotchas and Patterns

Local Domino-hosted LLMs run as **vLLM endpoints** behind the platform's
reverse proxy. The OpenAI-compatible API surface means you can use the
`openai` Python client to call them — but there are several rough edges
that bite first-time integrators.

This page covers the four most common ones.

## 1. The bearer token is short-lived — refresh per call

vLLM endpoints sit behind Domino auth. Workspaces and apps get a sidecar
token service at `http://localhost:8899/access-token` that issues bearer
tokens. **The token expires** (typically every few minutes) — caching the
OpenAI client at boot pins the original token into its `default_headers`
and the next call returns a `401`.

**Fix**: build the OpenAI client per call.

```python
import os, requests
from openai import OpenAI

DOMINO_TOKEN_URL = "http://localhost:8899/access-token"

def get_local_llm_client():
    """Build an OpenAI client routed at a Domino-hosted vLLM endpoint."""
    try:
        api_key = requests.get(DOMINO_TOKEN_URL, timeout=10).text
    except Exception:
        # Fallback for local development outside Domino
        api_key = os.environ.get("DOMINO_USER_API_KEY", "")

    base_url = os.environ["DOMINO_LLM_BASE_URL"]   # e.g. https://your-domino.com/endpoints/qwen35-4b/v1
    return OpenAI(base_url=base_url, api_key=api_key, timeout=90.0, max_retries=1)
```

Cost of rebuilding the client is roughly 1ms. Don't try to be clever
with token refresh detection — just rebuild.

## 2. `served_model_name` is often "." for vLLM endpoints

vLLM registers the model under whatever name it was launched with. In
Domino-hosted deployments this is frequently the literal string `"."`:

```python
completion = client.chat.completions.create(
    model=".",                    # NOT "qwen3-4b" or any friendly name
    messages=[...],
)
```

If you pass the friendly name (e.g. `"qwen3-4b"`) you'll get:
```
openai.NotFoundError: Error code: 404 - The model `qwen3-4b` does not exist
```

**Fix**: store `served_model_name` per roster entry and pass it as
`model=` at the call site. The roster entry has both:

```yaml
- key: qwen35-4b                      # Identifier used by app code
  label: "Qwen3-4B (local)"           # Display name in UI
  served_model_name: "."              # The string vLLM actually expects
```

Verify what vLLM expects with a `GET /v1/models` against your endpoint.

## 3. Qwen-specific: the `enable_thinking` chat-template flag

Qwen3 builds expose a chat-template variable `enable_thinking` that
suppresses or enables the model's `<think>...</think>` self-deliberation
preamble. vLLM forwards chat-template variables via the request body's
`chat_template_kwargs` field, which the OpenAI Python client surfaces as
`extra_body`:

```python
completion = client.chat.completions.create(
    model=".",
    messages=[...],
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

**This flag is Qwen-only.** Sending it to Mistral, DeepSeek, Gemma, or
Nemotron via Bedrock-Mantle returns:
```
openai.BadRequestError: Error code: 400 - Unknown extra_body field
```

**Fix**: gate it per provider. In a multi-provider codebase, add a
`send_qwen_thinking_flag: true` boolean to roster entries that are Qwen
builds, and a small helper:

```python
_THINKING_OFF = {"chat_template_kwargs": {"enable_thinking": False}}

def _extra_body_for(entry: dict) -> dict:
    return _THINKING_OFF if entry.get("send_qwen_thinking_flag") else {}
```

Why turn thinking *off*? Qwen's `<think>` blocks emit ~200-500 tokens of
internal monologue before the actual response — that's wall-clock
latency for the user, plus token cost on streamed responses. For tool
selection or short structured outputs, you almost always want it off.
Leave it on for free-form reasoning prompts where the deliberation is
genuinely useful.

## 4. Base URL via env var, default in YAML

Local vLLM endpoints get redeployed during environment upgrades — the
URL changes when the workspace ID / endpoint ID changes. Bake the
default into your config but always allow env override:

```yaml
- key: qwen35-4b
  base_url_env: DOMINO_LLM_BASE_URL
  base_url_default: "https://fsi-demo.domino-eval.com/endpoints/qwen35-4b/v1"
```

```python
base_url = os.environ.get(entry.get("base_url_env", ""), "") \
           or entry.get("base_url_default", "")
```

In Domino, set the env var via **Project Settings → Environment Variables**
or via `domino_project_settings.md` in newer workflows. CI / staging /
prod all override the default; the YAML default is what the README
points new developers at.

## 5. Streaming + token usage capture

To get prompt/completion token counts on streamed responses (so the
GenAI Eval Dashboard's `mlflow.chat.tokenUsage` is populated), pass
`stream_options={"include_usage": True}`:

```python
stream = client.chat.completions.create(
    model=served_name,
    messages=[...],
    stream=True,
    stream_options={"include_usage": True},
    extra_body=_extra_body_for(entry),
)

for chunk in stream:
    if not chunk.choices:
        # Final chunk — usage-only. autolog reads it directly.
        continue
    delta = chunk.choices[0].delta
    if delta and delta.content:
        yield delta.content
```

vLLM, Anthropic, and Bedrock-Mantle all honour `include_usage` in our
testing (Pierpoint Phase 0). The terminal usage chunk has no `choices`
entry so the consumer must skip it explicitly — otherwise you index
into `chunk.choices[0]` and crash on the last chunk.

See `STREAMING.md` for more.

## 6. Common errors and what they mean

| Error | Likely cause |
|-------|--------------|
| `401 Unauthorized` | Sidecar token expired — rebuild the OpenAI client per call |
| `404 model "X" does not exist` | `served_model_name` wrong; try `"."` |
| `400 Unknown extra_body field "chat_template_kwargs"` | Qwen flag sent to non-Qwen provider — gate per-entry |
| `503` from `localhost:8899` | Sidecar token service not running. Use `DOMINO_USER_API_KEY` env fallback |
| Hangs on first call (10-30s) | vLLM cold start — first request after idle. Subsequent calls fast |
| `openai.APITimeoutError` | Endpoint pod restarted. Increase client `timeout=` and verify endpoint health in UI |

## Reference

`app/api/chatbot.py:1285` (`_get_llm_client`) and
`app/api/chatbot.py:1269-1274` (the Qwen thinking-flag comment block)
in the Pierpoint Credit Sales demo.
