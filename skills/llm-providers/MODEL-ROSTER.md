# Model Roster — Config-Driven Multi-Provider Routing

A **model roster** is a list of LLM provider entries the application can pick
between at runtime. Each entry is a dict carrying everything `_get_llm_client()`
needs to construct a working OpenAI client for that provider: base URL, auth
mechanism, model ID, and any provider-specific request-body knobs.

This is the pattern that lets a user pick a model from a UI dropdown and have
the agent route the next request to that provider — no per-provider branching
in the call sites.

## YAML schema

```yaml
# agent_config.yaml
models:
  default_key: qwen35-4b
  roster:
    - key: qwen35-4b                  # Stable identifier — UI uses this
      label: "Qwen3-4B (local)"       # Display name
      provider: domino                # one of: domino | anthropic | bedrock-mantle
      base_url_env: DOMINO_LLM_BASE_URL
      base_url_default: "https://fsi-demo.domino-eval.com/endpoints/qwen35-4b/v1"
      served_model_name: "."          # vLLM quirk: endpoint registered as "."
      send_qwen_thinking_flag: true   # Qwen-only knob — see LOCAL-VLLM.md
      context_window: 8192

    - key: claude-sonnet-4-6
      label: "Claude Sonnet 4.6"
      provider: anthropic
      base_url_default: "https://api.anthropic.com/v1/"
      api_key_env: ANTHROPIC_API_KEY
      context_window: 200000

    - key: deepseek.v3.2
      label: "DeepSeek V3.2"
      provider: bedrock-mantle
      base_url_env: AWS_BEDROCK_BASE_URL
      api_key_env: AWS_BEDROCK_API_KEY
      context_window: 128000
```

`base_url_env` lets you override `base_url_default` via environment. The
default is fine for committed configs; the env var lets staging/prod point
at different gateways without editing the file.

## Loading the roster

```python
import os, yaml

def _load_roster(path: str) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    models_cfg = cfg.get("models") or {}
    roster = models_cfg.get("roster") or []
    by_key = {m["key"]: m for m in roster}
    return {
        "default_key": models_cfg.get("default_key") or roster[0]["key"],
        "models_by_key": by_key,
        "order": [m["key"] for m in roster],
    }

_ROSTER = _load_roster("agent_config.yaml")
DEFAULT_MODEL_KEY = os.environ.get("AGENT_DEFAULT_MODEL_KEY", _ROSTER["default_key"])
```

`AGENT_DEFAULT_MODEL_KEY` is a useful escape hatch: in production you may
want to force everyone to a specific provider regardless of what the YAML
says.

## Resolving + building the client

```python
def _resolve_model(model_key: str | None) -> dict:
    """Look up the roster entry; default if missing/unknown."""
    key = model_key or DEFAULT_MODEL_KEY
    entry = _ROSTER["models_by_key"].get(key)
    if entry is None:
        entry = _ROSTER["models_by_key"][DEFAULT_MODEL_KEY]
    return entry

def _get_llm_client(model_key: str | None = None):
    """Return (client, served_model_name, entry) for the chosen provider."""
    from openai import OpenAI
    import requests
    entry = _resolve_model(model_key)

    base_url = (
        os.environ.get(entry.get("base_url_env", ""), "")
        or entry.get("base_url_default", "")
    )
    provider = entry.get("provider")

    if provider == "domino":
        # Sidecar issues short-lived bearer tokens — refresh per call.
        try:
            api_key = requests.get("http://localhost:8899/access-token", timeout=10).text
        except Exception:
            api_key = os.environ.get("DOMINO_USER_API_KEY", "")
    elif provider == "anthropic":
        api_key = os.environ.get(entry.get("api_key_env", "ANTHROPIC_API_KEY"), "")
    else:  # bedrock-mantle (or any OpenAI-compat gateway)
        api_key = os.environ.get(entry.get("api_key_env", ""), "") \
                  or os.environ.get("OPENAI_API_KEY", "")

    served_name = entry.get("served_model_name") or entry["key"]
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=90.0, max_retries=1)
    return client, served_name, entry
```

**Why build the client per call instead of caching it?** The Domino
provider's bearer token is short-lived (the sidecar reissues every few
minutes). Caching the OpenAI client at boot pins the original token
into its `default_headers` and the next call 401s after expiry.
Construction cost is negligible (~1ms); always rebuild.

## Per-provider request extras

Some providers accept extra request-body knobs that others reject with `400`.
Wrap them in a per-entry helper so call sites don't have to know:

```python
_THINKING_OFF = {"chat_template_kwargs": {"enable_thinking": False}}

def _extra_body_for(entry: dict) -> dict:
    if entry.get("send_qwen_thinking_flag"):
        return _THINKING_OFF
    return {}
```

The OpenAI client passes `extra_body` straight through into the request
body. vLLM forwards `chat_template_kwargs` to the underlying chat
template. Anthropic / Bedrock-Mantle reject this key with a 400 — the
flag is **only** safe to send to a provider that registered for it.

## Wiring it into a call site

```python
def _call_llm(prompt: str, model_key: str | None = None, max_tokens: int = 1024) -> str:
    client, served_name, entry = _get_llm_client(model_key)
    completion = client.chat.completions.create(
        model=served_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        timeout=90.0,
        extra_body=_extra_body_for(entry),
    )
    return completion.choices[0].message.content or ""
```

Same call site for every provider. Provider-specific behaviour is encoded
once, in the YAML and `_extra_body_for()`.

## UI-driven model selection

Pass the user's model choice down to the call site:

```python
# FastAPI route
@router.post("/chat")
def chat(req: ChatRequest):
    return _call_llm(req.prompt, model_key=req.model_key or DEFAULT_MODEL_KEY)
```

The UI gets the available list from `_ROSTER["order"]` (or expose a
`/api/models` endpoint that returns the roster minus secrets). When the
user changes the dropdown, subsequent requests carry the new `model_key`
and the routing happens server-side — no provider logic in the browser.

## Failure handling — fail loud, don't silently switch

In the credit-sales demo we deliberately surface the *failing model's
name* in the error rather than silently falling back to a different
provider:

```python
try:
    client, served_name, entry = _get_llm_client(model_key)
    completion = client.chat.completions.create(...)
    return completion.choices[0].message.content or ""
except Exception as e:
    failing_key = model_key or DEFAULT_MODEL_KEY
    return (
        f"⚠️ **{failing_key}** failed: {type(e).__name__}. "
        "Pick a different model from the switcher to retry."
    )
```

Why no auto-fallback?
- During a model-comparison demo, silently swapping to another provider
  hides the very thing the audience came to see.
- In production, the salesperson needs to know *which* provider failed
  to triage (rate limits, cold starts, network issues are all provider-
  specific).

If you want belt-and-braces for a non-demo path, add a single retry on
`HTTP 5xx` only (don't blanket-retry — 4xx is your bug, not theirs).

## Reference

Pierpoint Credit Sales: `app/agent_config.yaml` and `app/api/chatbot.py`
(see `_load_roster()` near line 49, `_get_llm_client()` near line 1285).
