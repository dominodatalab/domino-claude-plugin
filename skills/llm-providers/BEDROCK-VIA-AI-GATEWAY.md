# AWS Bedrock via Domino AI Gateway

Domino's AI Gateway exposes AWS Bedrock models behind an
**OpenAI-compatible** URL. Application code calls them with the standard
`openai` client — same shape as Anthropic direct or local vLLM. Domino
handles AWS credential rotation, audit logging, and per-endpoint access
control on the platform side.

This page is the **developer's view** — how to call Bedrock from Python
agent code via the Gateway. For setting up Gateway endpoints, managing
keys, or controlling access, see the `domino-ai-gateway` skill.

## Why route Bedrock through AI Gateway?

| | Direct AWS SDK (`boto3.client("bedrock-runtime")`) | Via Domino AI Gateway |
|---|---|---|
| AWS credentials | Per-user IAM role, distributed | Centralised, never seen by app code |
| Request shape | Bedrock-native (varies per model family) | OpenAI-compat (uniform) |
| Audit / access control | AWS CloudTrail | Domino Gateway logs + per-endpoint access list |
| Tracing | Need `mlflow.boto3.autolog()` (limited) | `mlflow.openai.autolog()` covers it |
| Multi-provider codebase | Branch on `boto3` vs `openai` everywhere | Single client class |

For multi-provider Domino agent code, the Gateway is the natural choice.

## Roster entry

```yaml
- key: deepseek.v3.2
  label: "DeepSeek V3.2"
  provider: bedrock-mantle              # Internal label for the gateway-routed catalog
  base_url_env: AWS_BEDROCK_BASE_URL    # Gateway base URL
  api_key_env: AWS_BEDROCK_API_KEY      # Gateway-issued bearer
  context_window: 128000
```

The `key` field on Gateway-routed entries should match the **model ID
that the Gateway endpoint expects** — typically `<vendor>.<model-id>`,
matching AWS Bedrock's model identifiers. Common ones at time of writing:

| Roster `key` | Vendor / model |
|--------------|----------------|
| `deepseek.v3.2` | DeepSeek V3.2 |
| `mistral.mistral-large-3-675b-instruct` | Mistral Large 3 |
| `google.gemma-3-12b-it` | Google Gemma 3 12B (Instruct) |
| `nvidia.nemotron-super-3-120b` | NVIDIA Nemotron Super 3 120B |
| `qwen.qwen3-32b` | Qwen 3 32B |
| `openai.gpt-oss-120b` | OpenAI GPT-OSS 120B |

The exact catalog depends on what your Gateway admin has provisioned —
check **Endpoints → Gateway LLMs** in the Domino UI for the live list.

## Building the client

```python
import os
from openai import OpenAI

def get_bedrock_gateway_client():
    """OpenAI client routed at the Domino AI Gateway's Bedrock endpoint."""
    base_url = os.environ.get("AWS_BEDROCK_BASE_URL")
    api_key  = os.environ.get("AWS_BEDROCK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError(
            "AWS_BEDROCK_BASE_URL and AWS_BEDROCK_API_KEY must be set "
            "(see Domino Project Settings → Environment Variables)"
        )
    return OpenAI(base_url=base_url, api_key=api_key, timeout=90.0, max_retries=1)
```

The `OPENAI_API_KEY` fallback is a local-dev convenience: developers
can run the same code against a personal OpenAI key on their laptop
without setting the Bedrock env vars. In Domino, only `AWS_BEDROCK_*`
should be set.

## Calling a Bedrock model

```python
client = get_bedrock_gateway_client()

completion = client.chat.completions.create(
    model="deepseek.v3.2",                       # Roster key == Bedrock model ID
    messages=[
        {"role": "system", "content": "You are a credit sales assistant."},
        {"role": "user", "content": "Summarise today's IOIs."},
    ],
    max_tokens=1024,
)

print(completion.choices[0].message.content)
```

Same shape as every other provider in this skill. The Gateway
translates the OpenAI-shaped request into the Bedrock-native format
required by each model family (Claude on Bedrock vs Mistral on Bedrock
vs Llama on Bedrock all have different native shapes — the Gateway
hides this).

## Streaming + token usage

Streaming works on every Gateway endpoint; usage capture works for
every endpoint we've tested:

```python
stream = client.chat.completions.create(
    model="deepseek.v3.2",
    messages=[...],
    max_tokens=2048,
    stream=True,
    stream_options={"include_usage": True},
)

for chunk in stream:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    if delta and delta.content:
        yield delta.content
```

In Pierpoint Phase 0 testing, all six Bedrock-Mantle entries in the
roster (DeepSeek V3.2, Mistral Large 3, Gemma 3 12B, Nemotron Super 3
120B, Qwen 3 32B, GPT-OSS 120B) returned valid usage on the terminal
chunk. If a future model doesn't, the trace's `mlflow.chat.tokenUsage`
will be empty and you'll see it as a gap on the Eval Dashboard.

## Tracing setup

Identical to every other OpenAI-compatible provider — wrap once at app
boot:

```python
import mlflow
mlflow.openai.autolog()
```

This works because the Gateway *is* an OpenAI-compatible interface from
the client's perspective. Spans for Bedrock models look the same as
Anthropic-direct spans look the same as local-vLLM spans — comparable
on latency, tokens, and cost.

## Adding a new Bedrock model to the roster

1. **Provision the endpoint in Gateway** (admin task — see
   `domino-ai-gateway` skill). Note the model ID exactly as it
   appears in the Gateway UI.
2. **Add to `agent_config.yaml`**:
   ```yaml
   - key: <vendor>.<model-id>            # Match Gateway exactly
     label: "Friendly Name (Provider)"
     provider: bedrock-mantle
     base_url_env: AWS_BEDROCK_BASE_URL
     api_key_env: AWS_BEDROCK_API_KEY
     context_window: <from model card>
   ```
3. **Test with a one-shot probe** before exposing to the UI:
   ```python
   client, served, entry = _get_llm_client("<vendor>.<model-id>")
   r = client.chat.completions.create(
       model=served, messages=[{"role":"user","content":"Hello"}], max_tokens=20
   )
   print(r.choices[0].message.content, r.usage)
   ```
4. **Probe with `stream=True`** as well — some models work on non-stream
   but choke on streaming; better to find out before a demo.

## Common errors

| Error | Likely cause |
|-------|--------------|
| `401 invalid api key` | `AWS_BEDROCK_API_KEY` not set or revoked. Check Gateway endpoint settings |
| `403 endpoint X not authorized` | Your user/team isn't on the Gateway endpoint's access list. Ask admin |
| `404 model "X" not found` | Roster `key` doesn't match the Gateway's model ID. Spelling matters (`deepseek.v3.2` vs `deepseek-v3.2`) |
| `400 max_tokens too high` | Some Bedrock models have lower per-request `max_tokens` caps than their context window suggests |
| `429 Throttling` | AWS Bedrock account-level throttling. Retry with exponential backoff or pick a different model |
| Long cold start (10-30s) | Some Bedrock models have warm-up latency on first request. Subsequent calls are fast |

## What about Claude on Bedrock?

If the Gateway has a Claude-on-Bedrock endpoint, treat it as a Bedrock
roster entry — `provider: bedrock-mantle`, model ID like
`anthropic.claude-sonnet-4-6-v1:0`. The advantage over Anthropic direct
is centralised credential management; the disadvantage is slightly
higher latency from the extra hop.

The credit-sales demo deliberately includes both Claude flavours to
let the audience compare:
- `claude-sonnet-4-6` — direct Anthropic API
- (Optional) `anthropic.claude-sonnet-4-6` — same model via Bedrock-Mantle

Same answers, different latency profiles, different audit trails.

## Reference

`app/agent_config.yaml` (the six `bedrock-mantle` roster entries) and
`app/api/chatbot.py:1311-1317` (the bedrock-mantle branch in
`_get_llm_client()`) in the Pierpoint Credit Sales demo.
