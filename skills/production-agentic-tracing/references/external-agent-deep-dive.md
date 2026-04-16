# External Agent Tracing — Deep Dive

This reference covers tracing for agents running **outside Domino**: AWS AgentCore, any OTel-instrumented agent, or any cloud runtime that cannot reach Domino's MLflow sidecar.

---

## Why External Agents Can't Write to Domino MLflow Directly

### Constraint 1 — JWT Authentication Wall

Domino's external MLflow REST API requires a cryptographically signed `X-Domino-Execution` JWT in every write request. This JWT is only issued within a running Domino execution context (job, app, workspace). There is no external endpoint to obtain one.

Inside Domino, `MLFLOW_TRACKING_URI=http://127.0.0.1:8768` points to the local sidecar, which bypasses JWT entirely. That sidecar is only accessible from within Domino's cluster — it's not reachable from external networks.

### Constraint 2 — No OTLP Ingestion Endpoint (Current Domino Versions)

Sending OTel spans directly from an external agent to Domino via `OTLP/HTTP` (`/v1/traces`) returns 404 on all candidate paths. No OTLP collector is exposed externally. **Dead end — do not re-explore.**

### Constraint 3 — No Jobs REST API Trigger (Current Domino Versions)

Triggering a Domino job from an external agent via REST API (to have the job log traces) also returns 404 on all known paths. **Dead end — do not re-explore.**

---

## The Solution: OTel Span Piggybacking

Since the external agent can't push trace data to Domino, it carries the trace data inside its response payload. The Domino App server (running inside Domino) receives the response, extracts the spans, and logs them to MLflow via the sidecar.

### Data flow

```
External Agent (AgentCore / AWS / GCP / any runtime)
  1. _span_collector.reset()         ← clear prior spans
  2. run_agent(prompt)               ← Strands emits OTel spans → _SpanCollector buffers them
  3. serialize spans                 ← convert OTel span objects to JSON-serializable dicts
  4. return {"response": "...", "spans": [...]}   ← carry spans in response body

                  ↓ HTTP / AWS SDK call ↓

Domino App (app_server.py — inside Domino)
  5. parse response JSON             ← defensively, with _fix_escapes() + _try_parse()
  6. @add_tracing parent span active (agentcore-invoke)
  7. _replay_spans_as_mlflow_spans() ← replay each span as mlflow.start_span() child
     └─ set mlflow.chat.tokenUsage on LLM spans only
  8. log_evaluation("total_tokens")  ← optional custom column
  9. Experiment Manager + Performance tab updated ✓
```

---

## Serializing OTel Spans (External Agent Side)

The `_serialize_span()` function converts an OTel `ReadableSpan` to a JSON-safe dict. Key fields to capture:

| Field | Source | Notes |
|-------|--------|-------|
| `name` | `span.name` | Used to classify LLM vs AGENT on replay |
| `trace_id` | `span.context.trace_id` | Format as 32-char hex |
| `span_id` | `span.context.span_id` | Format as 16-char hex |
| `parent_span_id` | `span.parent.span_id` | `None` for root span |
| `start_time_ns` | `span.start_time` | Nanoseconds since epoch |
| `end_time_ns` | `span.end_time` | Nanoseconds since epoch |
| `duration_ms` | Derived | `(end - start) / 1e6` |
| `attributes` | `dict(span.attributes or {})` | Includes `gen_ai.*` token counts |
| `status_code` | `span.status.status_code.name` | `"OK"`, `"ERROR"`, `"UNSET"` |
| `events` | `span.events` | Each event: name, timestamp_ns, attributes |

Token data lives in `attributes["gen_ai.usage.input_tokens"]` and `attributes["gen_ai.usage.output_tokens"]`.

---

## Replaying Spans (Domino App Side)

### MLflow span type classification

```python
is_llm = "chat" in name.lower() or "llm" in name.lower()
span_type = SpanType.LLM if is_llm else SpanType.AGENT
```

Strands span names to expect from a typical invocation:
- `chat` → LLM call (SpanType.LLM) — carries token counts in `gen_ai.*` attributes
- `execute_event_loop_cycle` → AGENT span — carries rolled-up token totals (do NOT set tokenUsage here)
- `invoke_agent Strands Agents` → AGENT span — root Strands span (do NOT set tokenUsage here)

### Token count handling

Strands propagates (`rolls up`) token totals from child LLM spans to parent AGENT spans. When replaying flat:

```
agentcore-invoke (add_tracing parent)
  ├─ chat                         gen_ai.usage.input_tokens=150, output_tokens=80
  ├─ execute_event_loop_cycle     gen_ai.usage.input_tokens=150, output_tokens=80  ← rolled up
  └─ invoke_agent Strands Agents  gen_ai.usage.input_tokens=150, output_tokens=80  ← rolled up
```

If you set `mlflow.chat.tokenUsage` on all three, MLflow sums them → 3× actual usage.
Only set it on spans where `is_llm=True`.

### MLflow version compatibility

```python
_HAS_SPAN_API = hasattr(mlflow, "start_span")   # requires MLflow 3.2.0+
```

If `_HAS_SPAN_API=False` (older MLflow), fall back to `mlflow.start_run(nested=True)` per span. This produces separate nested runs rather than a trace tree, but still captures the data.

---

## AgentCore-Specific Details

### Client invocation pattern

```python
from bedrock_agentcore_starter_toolkit.services.runtime import BedrockAgentCoreClient

client = BedrockAgentCoreClient("us-east-2")
response = client.invoke_endpoint(
    agent_arn="arn:aws:bedrock-agentcore:us-east-2:<account>:runtime/<name>",
    payload=json.dumps({"prompt": prompt}),
    session_id=session_id,
)
chunks = response.get("response", [])
```

### Double-encoding and bytes

AgentCore wraps the agent's return value in an additional JSON string on the first call. On the second and subsequent calls within a session, chunks are returned as bytes.

```python
raw = "".join(
    c.decode("utf-8") if isinstance(c, bytes) else str(c)
    for c in chunks
)
data = json.loads(raw)
if isinstance(data, str):        # first call: double-encoded
    data = json.loads(data)
```

### Debugging: `__debug_tracing__` probe

Send `"__debug_tracing__"` as the prompt to your `invoke()` handler. Return the span collector's current state as JSON without making an LLM call. Useful for verifying spans are being captured before wiring up the full pipeline:

```python
def invoke(payload, context):
    if payload.get("prompt") == "__debug_tracing__":
        return json.dumps({
            "response": "debug",
            "spans": [_serialize_span(s) for s in _span_collector.collect()],
            "span_count": len(_span_collector._spans),
        })
    # ... normal path
```

---

## OpenTelemetry-Instrumented External Agents (Non-Strands)

If your external agent uses a different OTel-compatible framework (LangChain with OTel, custom OTel instrumentation, etc.), the same piggybacking pattern applies:

1. Install a `_SpanCollector` (same `SpanExporter` subclass) as a `SimpleSpanProcessor` on the `TracerProvider`.
2. Ensure your framework sends spans to the same `TracerProvider` (e.g., `trace.set_tracer_provider(provider)` globally, or pass the provider to your framework's setup function).
3. Reset the collector at the start of each invocation, collect at the end, serialize, and return in the response payload.
4. The Domino App server's `_replay_spans_as_mlflow_spans()` is framework-agnostic — it only looks at `name`, `attributes["gen_ai.*"]`, and `duration_ms`. Works with any OTel-compatible source.

**Span name convention for token classification:** The replay logic checks `"chat" in name.lower() or "llm" in name.lower()` to identify LLM spans. If your framework uses different naming, update the filter accordingly in `_replay_spans_as_mlflow_spans()`.

---

## Fidelity Comparison

| Aspect | External piggybacking | Embedded (Strands in Domino) |
|--------|----------------------|------------------------------|
| Span hierarchy | Flat (all siblings) | Real parent-child tree |
| Token counts | Manual, LLM-spans-only filter required | Automatic via OTel bridge |
| `mlflow.chat.tokenUsage` | Set manually | Set automatically |
| Span events | Serialized + replayed | Native |
| Timing precision | From serialized ns timestamps (post-hoc) | Real-time |
| Parse failures | JSON escaping issues can drop spans | No serialization step |
| Latency overhead | Response payload grows with span count | Zero |
| External runtime requirement | Any runtime that can return JSON | Must run inside Domino |

---

## Recommended Testing Sequence

1. Deploy external agent. Send `"__debug_tracing__"` → verify `span_count > 0` in response.
2. Wire `app_server.py`. Print `result["spans"]` count after `_call_external_agent()`.
3. Verify token attributes: print `attrs.get("gen_ai.usage.input_tokens")` on the `chat` span.
4. Check Performance tab: "Input tokens (k)" / "Output tokens (k)" columns should be non-zero.
5. Check Experiment Manager → Traces tab: should show the span tree under `agentcore-invoke`.
6. Verify token totals are not doubled: expected = LLM span tokens only, not 2× or 3×.
