# Streaming + Token Usage Capture Across Providers

Streamed responses are essential for any chat-style UI (typing indicator,
incremental display, perceived latency reduction). The OpenAI Python
client's streaming shape is uniform across all the providers in this
skill, but token-usage capture has one wrinkle worth knowing.

## The pattern

```python
stream = client.chat.completions.create(
    model=served_name,
    messages=[...],
    max_tokens=2048,
    stream=True,
    stream_options={"include_usage": True},
    extra_body=_extra_body_for(entry),
)

for chunk in stream:
    if not chunk.choices:
        # Final chunk — usage block lives here, no content to yield
        continue
    delta = chunk.choices[0].delta
    if delta and delta.content:
        yield delta.content
```

Two things to notice:

1. **`stream_options={"include_usage": True}`** asks the gateway to send
   a final chunk with `prompt_tokens` and `completion_tokens`.
2. **The terminal chunk has no `choices` entry.** Skip it explicitly,
   otherwise `chunk.choices[0]` will `IndexError` on the last iteration.

## Why include_usage matters

Without it, streamed responses don't populate
`mlflow.chat.tokenUsage` on the Completions span. The Eval Dashboard's
**Average tokens by model** chart shows zero for streamed traces, which
makes per-model cost comparisons useless.

In credit-sales (`Phase 0` testing), every roster provider honoured
`include_usage`:
- Domino-hosted vLLM (Qwen3 family)
- Anthropic direct (`claude-sonnet-4-6`, `claude-opus-4-7`)
- Bedrock-Mantle (DeepSeek, Mistral, Gemma, Nemotron, Qwen, GPT-OSS)

When you add a new provider to the roster, run a one-shot probe with
`stream=True, include_usage=True` and verify the terminal chunk has a
non-null `usage`:

```python
stream = client.chat.completions.create(
    model=served_name,
    messages=[{"role":"user","content":"Hello"}],
    max_tokens=20,
    stream=True,
    stream_options={"include_usage": True},
)
chunks = list(stream)
final = chunks[-1]
assert final.usage is not None, f"{served_name} did not return usage on terminal chunk"
print(f"{served_name}: prompt={final.usage.prompt_tokens}, completion={final.usage.completion_tokens}")
```

If a provider returns `None`, the trace will have empty usage — surface
it as a known gap rather than letting it silently corrupt cost numbers.

## Non-streamed token usage

For non-streamed responses, usage is on the response object directly:

```python
completion = client.chat.completions.create(
    model=served_name,
    messages=[...],
    max_tokens=2048,
)
print(f"prompt={completion.usage.prompt_tokens}, completion={completion.usage.completion_tokens}")
```

`mlflow.openai.autolog()` reads this automatically — no extra code
needed in the call site.

## Streaming + tracing interaction

The `@add_tracing` decorator and `mlflow.openai.autolog()` both work
with streamed responses. You don't need to special-case streaming in
your traced functions:

```python
from domino.agents.tracing import add_tracing

@add_tracing(name="streamed_chat", autolog_frameworks=["openai"])
def stream_chat(prompt: str, model_key: str):
    client, served, entry = _get_llm_client(model_key)
    for chunk in _call_llm_streaming(client, served, prompt, entry):
        yield chunk
```

The Completions span captures the full request, response, and usage
from the terminal chunk. The span duration reflects the full stream
length, which is what you want for latency comparisons.

## Common gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| `IndexError` on last chunk | Forgot to skip chunks with no `choices` | `if not chunk.choices: continue` |
| Usage shows zero in Eval Dashboard for streamed traces | Missing `stream_options={"include_usage": True}` | Add it to all streaming calls |
| Streamed response cuts off early | Provider's `max_tokens` cap hit | Inspect `finish_reason` on the last chunk with `choices` — `length` means truncated |
| First-byte latency 5-30s | Cold start (vLLM endpoint or Bedrock model). | Warm with a `SELECT 1`-style probe at app boot, or accept the cold-start hit |
| Token counts much higher than expected | Qwen `<think>` tokens being counted (`enable_thinking=True`) | Pass `enable_thinking=False` for non-reasoning prompts (see LOCAL-VLLM.md) |

## Reference

`app/api/chatbot.py:1360-1404` (`_call_llm_streaming`) in the Pierpoint
Credit Sales demo. The `if not chunk.choices: continue` line is on 1392.
