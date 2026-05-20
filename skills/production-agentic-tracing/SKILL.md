---
name: agentic-tracing
description: >
  Complete guide for production agentic tracing in Domino Data Lab using MLflow and OpenTelemetry.
  Use this skill whenever the user mentions: agent tracing, MLflow traces, Domino Performance tab,
  OTel spans, span piggybacking, DominoRun, add_tracing, init_tracing, AgentCore tracing,
  external agent observability, token counts in traces, Strands tracing, or any question about
  wiring up observability/governance for an agent running inside or outside Domino.
  This skill covers both embedded agents (Strands running directly in Domino) and externally-deployed
  agents (AgentCore, OTel-instrumented agents, or any agent running outside Domino's network).
---

# Agentic Tracing — Production Reference

## Overview

There are two tracing architectures depending on where the agent runs:

| Mode | Agent location | Tracing mechanism |
|------|---------------|-------------------|
| **Embedded** | Inside Domino App | `init_tracing()` OTel-to-MLflow bridge — automatic, no manual instrumentation |
| **External** | Outside Domino (AgentCore, any cloud runtime) | OTel Span Piggybacking — serialize spans in response, replay inside Domino |

The Performance tab and Experiment Manager both read from `agent_experiment_{DOMINO_APP_ID}`. All MLflow writes **must happen from inside Domino** — external agents cannot write directly.

---

## Part 1: Embedded Agent Tracing (Strands inside Domino)

### Architecture

```
User → Domino App (FastAPI)
         DominoRun() — establishes run in agent_experiment_{DOMINO_APP_ID}
           @add_tracing("agent-invoke") — parent span
             Strands agent runs here
             init_tracing() OTel-to-MLflow bridge captures all Strands spans automatically
                ├─ chat                        SpanType.LLM  (tokens, duration)
                ├─ execute_event_loop_cycle    SpanType.AGENT
                └─ invoke_agent Strands Agents SpanType.AGENT
       → Domino Experiment Manager (MLflow) ✓
       → Performance tab ✓
```

### Initialization (order matters)

```python
import mlflow
mlflow.set_tracking_uri("http://127.0.0.1:8768")   # local sidecar — always this URI inside Domino

# Step 1: init_tracing() FIRST — sets up OTel-to-MLflow bridge AND sets active experiment
#         to agent_experiment_{DOMINO_APP_ID} in production.
from domino.agents.tracing import init_tracing, add_tracing
from domino.agents.tracing._util import is_agent as _is_agent_mode
from domino.agents.logging import DominoRun
init_tracing()
_IS_PROD = _is_agent_mode()   # True when DOMINO_AGENT_IS_PROD=true AND DOMINO_APP_ID are set

# Step 2: Dev only — set a visible experiment for Experiment Manager.
#         NEVER do this unconditionally; in production it breaks the Performance tab.
if not _IS_PROD:
    mlflow.set_experiment("my-agent-traces")
```

### Per-request flow

```python
@app.post("/api/invoke")
def invoke(req):
    prompt     = req.prompt
    session_id = req.session_id or str(uuid.uuid4())

    # DominoRun with NO experiment_name — inherits whatever init_tracing() set as active.
    # Production → agent_experiment_{DOMINO_APP_ID} → Performance tab ✓
    # Dev        → your dev experiment              → Experiment Manager ✓
    # Also calls mlflow.create_external_model(model_type="Agent") — required for Performance tab.
    with DominoRun(agent_config_path="agent_config.yaml"):
        answer = _invoke_agent(prompt, session_id)
    return {"answer": answer}


def _invoke_agent(prompt: str, session_id: str) -> str:
    agent  = _make_agent()          # MUST be fresh per call — see Gotcha #8
    result = agent(prompt)          # Strands OTel spans captured automatically
    return str(result)

# Wrap AFTER init_tracing() — @add_tracing nests inside DominoRun's run context.
_invoke_agent = add_tracing(name="agent-invoke", autolog_frameworks=["openai"])(_invoke_agent)
```

### agent_config.yaml (required)

```yaml
name: my-agent
version: "1.0"
model_endpoint: https://<domino-host>/models/<endpoint-id>/latest/model
```

`DominoRun.__log_params()` passes this to `mlflow.create_external_model()`. Without it, `create_external_model` gets empty params and the Performance tab shows **"Failed to fetch dataset details — unknown is not a valid ID"**.

### How Performance tab qualification works

All six conditions must be true:

1. `DOMINO_AGENT_IS_PROD=true` — auto-injected by Domino Agent infrastructure
2. `DOMINO_APP_ID=<id>` — auto-injected by Domino Agent infrastructure
3. `init_tracing()` called first — creates/finds `agent_experiment_{DOMINO_APP_ID}` and sets it active
4. `DominoRun()` called with **no** `experiment_name` — uses active experiment set by `init_tracing()`
5. `DominoRun()` calls `mlflow.create_external_model(model_type="Agent")` — registers as agent run
6. Performance tab filters by `mlflow.domino.app_id` tag — only runs in `agent_experiment_{DOMINO_APP_ID}` appear

---

## Part 2: External Agent Tracing (AgentCore / OTel agents outside Domino)

### Why external agents can't write to Domino MLflow directly

Three dead ends — do not re-explore:

1. **JWT wall** — Domino's external MLflow REST API requires a signed `X-Domino-Execution` JWT, only issued inside a running Domino execution context. `http://127.0.0.1:8768` (the local sidecar that bypasses JWT) is only reachable from within Domino's cluster.
2. **No OTLP ingestion** — Sending OTel spans via OTLP/HTTP (`/v1/traces`) returns 404 on all candidate paths on current Domino versions.
3. **No Jobs REST API** — Triggering a Domino job from an external agent to log traces also returns 404.

**Solution: OTel Span Piggybacking** — carry trace data inside the agent's JSON response; have the Domino App server log it.

### External agent: `_SpanCollector` pattern

```python
# agent.py (runs in AgentCore or any external runtime)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
import threading, json

class _SpanCollector(SpanExporter):
    """Buffers every completed OTel span for the current invocation."""
    def __init__(self):
        self._spans = []
        self._lock  = threading.Lock()

    def reset(self):
        with self._lock:
            self._spans = []

    def export(self, spans):
        with self._lock:
            self._spans.extend(spans)
        return SpanExportResult.SUCCESS

    def collect(self):
        with self._lock:
            return list(self._spans)

    def shutdown(self):
        pass

_span_collector = _SpanCollector()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(_span_collector))
trace.set_tracer_provider(provider)


def _serialize_span(span) -> dict:
    return {
        "name":           span.name,
        "trace_id":       format(span.context.trace_id, "032x"),
        "span_id":        format(span.context.span_id,  "016x"),
        "parent_span_id": format(span.parent.span_id,   "016x") if span.parent else None,
        "start_time_ns":  span.start_time,
        "end_time_ns":    span.end_time,
        "duration_ms":    (span.end_time - span.start_time) / 1e6
                          if span.end_time and span.start_time else 0,
        "attributes":     dict(span.attributes or {}),
        "status_code":    span.status.status_code.name if span.status else "UNSET",
        "events": [
            {"name": e.name, "timestamp_ns": e.timestamp, "attributes": dict(e.attributes or {})}
            for e in (span.events or [])
        ],
    }


def invoke(payload, context):
    _span_collector.reset()                                  # clear spans from prior invocation
    response_text = run_agent(payload["prompt"])
    spans = [_serialize_span(s) for s in _span_collector.collect()]
    return json.dumps({"response": response_text, "spans": spans})
```

> ⚠️ **Do NOT import or call `init_tracing()` in external agent code.** `init_tracing()` tries to connect to Domino's MLflow sidecar, which doesn't exist outside Domino's network. It will block or error on startup. Remove `dominodatalab[agents]` from the external agent's `requirements.txt`.

### Domino App server: span replay

```python
# app_server.py — inside Domino
import mlflow
try:
    from mlflow.entities import SpanType as _SpanType
    _HAS_SPAN_API = hasattr(mlflow, "start_span")
except ImportError:
    _SpanType = None
    _HAS_SPAN_API = False


def _replay_spans_as_mlflow_spans(spans: list, session_id: str):
    """Re-emit serialized OTel spans as MLflow trace-tree children.
    Must be called within an active @add_tracing context.
    Spans are replayed FLAT (all siblings) — parent-child hierarchy is lost.
    """
    for span_data in spans:
        attrs = span_data.get("attributes", {})
        name  = span_data.get("name", "agent-span")
        is_llm = "chat" in name.lower() or "llm" in name.lower()

        span_kw = {"name": name}
        if _SpanType:
            span_kw["span_type"] = _SpanType.LLM if is_llm else _SpanType.AGENT

        with mlflow.start_span(**span_kw) as mlf:
            for k, v in attrs.items():
                try:
                    mlf.set_attribute(k, v)
                except Exception:
                    pass

            # CRITICAL: only set mlflow.chat.tokenUsage on LLM spans.
            # Strands rolls token totals up to parent AGENT spans.
            # Flat replay means MLflow cannot deduplicate parent+child tokens —
            # setting tokenUsage on both causes 2× or 3× token counts.
            if is_llm:
                in_tok  = int(attrs.get("gen_ai.usage.input_tokens",  0))
                out_tok = int(attrs.get("gen_ai.usage.output_tokens", 0))
                if in_tok or out_tok:
                    mlf.set_attribute("mlflow.chat.tokenUsage", {
                        "input_tokens":  in_tok,
                        "output_tokens": out_tok,
                        "total_tokens":  in_tok + out_tok,
                    })

            mlf.set_attribute("duration_ms", float(span_data.get("duration_ms", 0)))
            mlf.set_attribute("session_id",  session_id)


def _invoke_agent(prompt: str, session_id: str) -> str:
    result = _call_external_agent(prompt, session_id)   # returns {"answer": str, "spans": list}

    if result["spans"]:
        if _HAS_SPAN_API:
            _replay_spans_as_mlflow_spans(result["spans"], session_id)
        else:
            _log_spans_as_runs(result["spans"], prompt, session_id)  # fallback for older MLflow

    # Optional: log total_tokens as a custom evaluation column.
    # MUST use the same LLM-span filter as mlflow.chat.tokenUsage — otherwise
    # total_tokens column will not equal input + output.
    from domino.agents.logging import log_evaluation
    llm_spans   = [s for s in result["spans"]
                   if "chat" in s.get("name","").lower() or "llm" in s.get("name","").lower()]
    total_input  = sum(int(s.get("attributes",{}).get("gen_ai.usage.input_tokens",  0)) for s in llm_spans)
    total_output = sum(int(s.get("attributes",{}).get("gen_ai.usage.output_tokens", 0)) for s in llm_spans)
    if total_input + total_output:
        active_span = mlflow.get_current_active_span()
        if active_span:
            log_evaluation(active_span.request_id, name="total_tokens",
                           value=float(total_input + total_output))

    return result["answer"]

_invoke_agent = add_tracing(name="agentcore-invoke")(_invoke_agent)
```

### Parsing the external agent response (defensive)

Some runtimes (e.g., `BedrockAgentCoreClient`) double-encode the return value or return bytes on 2nd+ calls. Always parse defensively:

```python
import re, json

def _fix_escapes(s: str) -> str:
    """Fix invalid JSON escape sequences common in LLM responses:
    regex patterns (\\d, \\w), Windows paths (\\Users\\), LaTeX (\\alpha).
    Double-escapes any \\X where X is not a valid JSON escape character.
    """
    s = s.replace("\\'", "'")                               # Strands span events use invalid \'
    s = s.replace('\\\n', '\\n')                            # literal newlines in strings
    s = re.sub(r'\\(?!["\\\\/bfnrtu])', r'\\\\', s)        # catch-all: double-escape orphaned \
    return s

def _try_parse(s: str, label: str = "") -> dict:
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        # Log position + context window for debugging
        start = max(0, e.pos - 40)
        print(f"[parse] {label} JSONDecodeError at pos {e.pos}: "
              f"...{repr(s[start:e.pos+20])}...")
        fixed = _fix_escapes(s)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e2:
            raise ValueError(f"[parse] {label} failed after fix_escapes: {e2}") from e2

def _regex_extract_response(s: str) -> str:
    """Last resort: extract response field via regex when json.loads fails entirely.
    Spans are dropped on this path — non-fatal.
    """
    m = re.search(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"', s)
    if m:
        return json.loads('"' + m.group(1) + '"')   # unescape the extracted string
    raise ValueError("Could not extract response field via regex")

def _call_external_agent(prompt: str, session_id: str) -> dict:
    # ... invoke external agent, collect raw response ...
    raw = "".join(
        c.decode("utf-8") if isinstance(c, bytes) else str(c)
        for c in chunks
    )
    try:
        data = _try_parse(raw, "outer")
        if isinstance(data, str):          # double-encoded — decode again
            data = _try_parse(data, "inner")
    except ValueError:
        # Last resort — drops spans but always recovers response text
        return {"answer": _regex_extract_response(raw), "spans": []}

    return {"answer": data["response"], "spans": data.get("spans", [])}
```

### Fidelity differences: external vs. embedded

| Aspect | External (span piggybacking) | Embedded (Strands in Domino) |
|--------|------------------------------|------------------------------|
| Span hierarchy | **Flat** — parent-child lost; all replayed as siblings | **Real tree** — hierarchy preserved |
| Token counts | Must filter to LLM spans only (double-count risk from AGENT rollup spans) | Automatic via OTel bridge |
| `mlflow.chat.tokenUsage` | Set manually in `_replay_spans_as_mlflow_spans` | Set automatically |
| Span events | Serialized + replayed manually | Passed through natively |
| Timing | Derived from serialized nanosecond timestamps | Real-time |
| Parse failures | JSON escape issues can drop spans | No serialization, no failures |

---

## Part 3: Quality Scoring (log_evaluation)

Add LLM-as-judge or other quality scores to any trace:

```python
from domino.agents.tracing import search_traces
from domino.agents.logging import log_evaluation

# After a DominoRun, find traces and score them
traces = search_traces(run_id=run_id)
for trace in traces.data:
    log_evaluation(trace_id=trace.id, name="response_quality", value=4.5)
```

`log_evaluation` creates **custom columns** in the Performance tab. It does NOT populate the built-in "Input/Output tokens (k)" columns — those require `mlflow.chat.tokenUsage` span attribute.

---

## Part 4: Environment Variables

### Auto-injected by Domino Agent infrastructure (app_server.py)

```bash
DOMINO_AGENT_IS_PROD=true               # triggers production tracing mode
DOMINO_APP_ID=<deployment-id>           # identifies the agent deployment
```

`_is_agent_mode()` returns `True` only when **both** are present.

### Optional overrides (app_server.py)

```bash
DOMINO_API_KEY=<64-char key>            # if absent, fetched from localhost:8899 sidecar
DOMINO_MODEL_URL=<endpoint url>         # override Domino-hosted model endpoint
```

### External agent container (e.g., AgentCore)

```bash
DOMINO_API_KEY=<64-char key>            # for calling Domino-hosted model endpoint
MLFLOW_TRACKING_URI=https://<domino-host>  # external URI (not the sidecar — can't reach it)
DOMINO_PROJECT_NAME=<project>
DOMINO_PROJECT_OWNER=<owner>
OTEL_SERVICE_NAME=<service-name>        # names your service in OTel spans
```

---

## Part 5: All Gotchas

For the full annotated gotcha list, see [`references/gotchas.md`](references/gotchas.md).

**The most critical ones at a glance:**

- ❌ **Never call `mlflow.set_experiment()` unconditionally** — only in `if not _IS_PROD` branches.
- ❌ **Never pass `experiment_name` to `DominoRun()` in production** — breaks Performance tab.
- ❌ **Never import `init_tracing()` in external agent code** — it tries to reach the Domino sidecar and will fail outside Domino's network.
- ❌ **Never set `mlflow.chat.tokenUsage` on AGENT-type spans** — Strands rolls token totals up from LLM spans to parent AGENT spans; flat replay causes double-counting.
- ❌ **Never reuse an `httpx.AsyncClient` across Strands invocations** — Strands uses `asyncio.run()` which closes the event loop, tearing down any client created in that loop.
- ❌ **Never re-install `requirements.txt` packages inside `install_deps()`** — causes `Permission denied: 'WHEEL'` temp file races from pip re-resolution.

---

## Part 6: Useful Diagnostics

```bash
# Check MLflow experiment for recent runs (run as Domino job or notebook)
python check_mlflow_runs.py

# Debug probe for external agents — returns span collector state without making an LLM call
# Send "__debug_tracing__" as the prompt to invoke() and inspect the returned JSON.
```

For more detail on architecture, token column mechanics, and the full bugs-fixed history, see:
- [`references/gotchas.md`](references/gotchas.md) — all gotchas with full context
- [`references/external-agent-deep-dive.md`](references/external-agent-deep-dive.md) — span piggybacking in detail
