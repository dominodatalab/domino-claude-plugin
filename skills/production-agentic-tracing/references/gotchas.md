# Agentic Tracing — Full Gotchas Reference

All gotchas from production development. Read before modifying any tracing code.

---

## Domino App (app_server.py) Gotchas

### 1. Never override `mlflow.set_experiment()` in production

`init_tracing()` sets the active experiment to `agent_experiment_{DOMINO_APP_ID}`. Calling `mlflow.set_experiment("anything")` unconditionally overwrites this and breaks the Performance tab.

**Pattern:**
```python
if not _IS_PROD:
    mlflow.set_experiment("my-dev-traces")   # dev only ✓
# Never: mlflow.set_experiment("x")          # unconditional = breaks Performance tab ✗
```

---

### 2. `DominoRun()` without `experiment_name` is correct in production

`DominoRun()` with no `experiment_name` inherits whatever experiment `init_tracing()` set as active. Passing `experiment_name=` explicitly forces writes to a different experiment — the Performance tab won't see them.

```python
# CORRECT in production:
with DominoRun(agent_config_path="agent_config.yaml"):
    ...

# WRONG in production — breaks Performance tab:
with DominoRun(experiment_name="agentcore-traces", agent_config_path="agent_config.yaml"):
    ...
```

---

### 3. `DominoRun()` with `experiment_name` is fine in dev

In dev mode (`_IS_PROD=False`) you can pass `experiment_name` to `DominoRun()` to target your dev experiment in Experiment Manager. Just never do this in a deployed Agent.

---

### 4. `DominoRun` per-request in production is intentional

In production, each request has its own Domino execution context. `DominoRun()` without `experiment_name` creates one new run per request, but they all land in `agent_experiment_{DOMINO_APP_ID}` — that's correct behavior. This is not a bug.

---

### 5. `agent_config.yaml` is required — missing it breaks the Performance tab UI

`DominoRun.__log_params()` reads `agent_config.yaml` and passes its contents to `mlflow.create_external_model(model_type="Agent")`. Without the file, `create_external_model` receives empty params and the UI shows:

> "Failed to fetch dataset details — unknown is not a valid ID"

The file must exist at the path passed to `DominoRun(agent_config_path=...)` at runtime.

---

### 6. `_IS_PROD` detection requires both env vars

`is_agent()` from `domino.agents.tracing._util` returns `True` only when **both** of these are set:

- `DOMINO_AGENT_IS_PROD=true`
- `DOMINO_APP_ID=<deployment-id>`

Both are injected automatically by Domino's Agent infrastructure at deployment time. In a regular Domino App (not deployed as a Deployment > Agent), neither will be set and `_IS_PROD=False`.

---

### 7. Token columns are populated automatically for embedded agents

When Strands runs directly inside Domino, `init_tracing()`'s OTel-to-MLflow bridge reads `gen_ai.*` span attributes from Strands and populates `mlflow.chat.tokenUsage` automatically. No manual instrumentation needed for the embedded case.

For external agents using span piggybacking, you must set `mlflow.chat.tokenUsage` manually inside `_replay_spans_as_mlflow_spans()`.

---

### 8. Create a fresh `httpx.AsyncClient` per Strands invocation

Strands uses `asyncio.run()` internally, which closes the event loop when it exits. Any `httpx.AsyncClient` created in that loop is torn down.

```python
# WRONG — breaks on 2nd+ call:
_client = httpx.AsyncClient(...)  # cached at module level

# CORRECT:
def _make_agent():
    client = httpx.AsyncClient(...)   # fresh every call
    model  = OpenAIModel(..., http_client=client)
    return Agent(model=model, ...)
```

Error you'll see if you reuse: `"Cannot send a request, as the client has been closed."`

---

### 9. Never set `mlflow.chat.tokenUsage` on AGENT-type spans (external agents)

Strands propagates (rolls up) token totals from child LLM spans to parent AGENT spans (`invoke_agent Strands Agents`, `execute_event_loop_cycle`). When replaying spans flat (all siblings), MLflow cannot deduplicate parent+child. Setting `tokenUsage` on both causes 2× or 3× token counts in the Performance tab.

**Rule:** Only set `mlflow.chat.tokenUsage` on spans where `"chat" in name.lower() or "llm" in name.lower()`.

---

### 10. `log_evaluation("total_tokens")` must use the same LLM-span filter as `mlflow.chat.tokenUsage`

If `total_tokens` sums all spans (including AGENT rollup spans) while `mlflow.chat.tokenUsage` only covers LLM spans, the total column will not equal input + output in the UI.

```python
# Filter consistently:
llm_spans = [s for s in spans if "chat" in s.get("name","").lower() or "llm" in s.get("name","").lower()]
total = sum(int(s.get("attributes",{}).get("gen_ai.usage.input_tokens", 0)) +
            int(s.get("attributes",{}).get("gen_ai.usage.output_tokens", 0)) for s in llm_spans)
```

---

### 11. Never re-install `requirements.txt` packages inside `install_deps()`

Domino runs `pip install -r requirements.txt` before `app.sh` launches. If `install_deps()` re-installs any of the same packages, pip re-resolves transitive dependencies against an already-modified environment, causing:

> `Permission denied: 'WHEEL'` (temp file race from version change, e.g., opentelemetry 1.40→1.41)

`install_deps()` should only contain packages that genuinely cannot go in `requirements.txt` — e.g., packages that need `--target` isolation or `--no-deps` for version pinning.

---

### 12. `@add_tracing` must wrap AFTER `init_tracing()` is called

`add_tracing` registers its OTel hooks at wrap time. If you call it before `init_tracing()`, the OTel-to-MLflow bridge isn't set up yet and the decorator won't capture spans correctly.

```python
init_tracing()                                           # Step 1
_invoke_agent = add_tracing(name="agent-invoke")(_invoke_agent)   # Step 2 — after init
```

---

### 13. `@add_tracing` nested runs only work when wrapped in `DominoRun()`

`@add_tracing` uses OTel internally. If you wrap a function with `@add_tracing` and call `mlflow.start_run(nested=True)` inside it, there is no MLflow parent context and the nested run is invisible. The fix is always to create the outer MLflow run context with `DominoRun()` first.

---

## External Agent Gotchas (AgentCore / OTel agents)

### 14. Do NOT import `init_tracing()` in external agent code

`init_tracing()` tries to connect to `http://127.0.0.1:8768`, which is Domino's local MLflow sidecar. This address doesn't exist outside Domino's cluster. Importing it in an external agent will block on startup or raise a connection error.

Remove `dominodatalab[agents]` from the external agent's `requirements.txt` entirely.

---

### 15. `BedrockAgentCoreClient` double-encodes the return value

`BedrockAgentCoreClient.invoke_endpoint()` wraps the agent's return value in an extra JSON string. Always check for double-encoding:

```python
data = json.loads(raw)
if isinstance(data, str):    # double-encoded — decode again
    data = json.loads(data)
```

---

### 16. `BedrockAgentCoreClient` returns bytes on 2nd+ call

On the first call, response chunks are strings. On the second and subsequent calls, chunks are `bytes`. Always decode:

```python
raw = "".join(
    c.decode("utf-8") if isinstance(c, bytes) else str(c)
    for c in chunks
)
```

---

### 17. JSON parse failures from LLM responses with special characters

LLM responses frequently contain character sequences that break JSON parsing when embedded inside a JSON string:

| Pattern | Example | Why it breaks |
|---------|---------|---------------|
| Regex patterns | `\d`, `\w`, `\s` | `\d` is not a valid JSON escape |
| Windows paths | `\Users\name` | `\U` / `\n` as path separator vs. newline |
| LaTeX | `\alpha`, `\beta` | `\a` is not a valid JSON escape |
| Strands span events | `\'` (apostrophes) | `\'` is not a valid JSON escape |
| Literal newlines | multi-line LLM output | unescaped newline inside a JSON string value |

Fix with the `_fix_escapes()` utility (see SKILL.md Part 2) and the multi-stage `_try_parse()` → `_regex_extract_response()` fallback chain.

---

### 18. Reset `_span_collector` at the start of every invocation

```python
def invoke(payload, context):
    _span_collector.reset()    # ← MUST be first — clears spans from prior invocation
    response_text = run_agent(payload["prompt"])
    spans = [_serialize_span(s) for s in _span_collector.collect()]
    return json.dumps({"response": response_text, "spans": spans})
```

If you forget `reset()`, spans from previous invocations accumulate and are reported with every response.

---

### 19. Span replay is flat — parent-child hierarchy is lost

When replaying serialized OTel spans inside `_replay_spans_as_mlflow_spans()`, all spans become siblings under the `@add_tracing` parent. The original `parent_span_id` relationships from the external agent are not re-created in MLflow. This is a known limitation of the piggybacking approach — accept it, don't try to reconstruct hierarchy.

---

## Frontend / App Gotchas

### 20. marked v4 `cleanUrl()` silently drops image URLs

marked v4's built-in `image()` renderer calls `cleanUrl(href)` internally, which returns `null` for some valid URLs and silently omits the `<img>` tag, showing only alt text.

**Fix:** Always override `image()` in `marked.use()`:
```javascript
marked.use({
  renderer: {
    image(href, title, text) {
      const safeHref  = (href  || "").replace(/"/g, "&quot;");
      const safeAlt   = (text  || "").replace(/"/g, "&quot;");
      const safeTitle = (title || "").replace(/"/g, "&quot;");
      return `<img src="${safeHref}" alt="${safeAlt}"${safeTitle ? ` title="${safeTitle}"` : ""}>`;
    }
  }
});
```

---

### 21. Images may be blocked by Domino's nginx CSP header

Domino's nginx layer can inject `Content-Security-Policy: img-src 'self'`, blocking external image URLs. Fix by adding middleware to override CSP:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class _ImageCSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "img-src * data: blob:"
        return response

app.add_middleware(_ImageCSPMiddleware)
```

---

### 22. Links inside the Domino app must open in a new tab

The app is served inside Domino's reverse-proxy iframe. Clicking a link without `target="_blank"` tries to load the external site inside the iframe; most sites refuse via `X-Frame-Options: SAMEORIGIN`.

**Fix:** Override `link()` in `marked.use()`:
```javascript
marked.use({
  renderer: {
    link(href, title, text) {
      return `<a href="${href}" target="_blank" rel="noopener noreferrer">${text}</a>`;
    }
  }
});
```

`noopener` prevents the new tab from accessing `window.opener`; `noreferrer` avoids leaking the Domino app URL.

---

### 23. Do not re-decode `\n`/`\t`/`\"` in the frontend

Once `_try_parse()` / `_fix_escapes()` correctly parses the backend response, `data.answer` already has real newlines and the literal two-character sequence `\n` where code examples need it (e.g., `# Using \n in a string`). Re-decoding `\n` → newline in the frontend corrupts code examples.

Only safe to keep: stripping surrounding quotes added as a safety net.

---

## MLFLOW_TRACKING_URI Gotchas

### 24. Use `se-demo.domino.tech`, not `apps.se-demo.domino.tech`

The MLflow sidecar is on the main Domino host. The `apps.` subdomain is for deployed apps and returns errors when used as a tracking URI.

```python
# CORRECT:
mlflow.set_tracking_uri("http://127.0.0.1:8768")   # inside Domino (always)

# EXTERNAL agent (cannot use sidecar):
# MLFLOW_TRACKING_URI=https://se-demo.domino.tech   # external host — but JWT required, see Constraint 1
```

---

## Bugs Fixed History

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `init_tracing()` blocked in AgentCore | Tries to connect to Domino sidecar (127.0.0.1:8768); not reachable outside Domino | Remove `dominodatalab[agents]` from external requirements.txt |
| MLFLOW_TRACKING_URI wrong hostname | Used `apps.se-demo.domino.tech` instead of `se-demo.domino.tech` | Corrected hostname |
| AgentCore response showed raw JSON in UI | `BedrockAgentCoreClient` double-encodes; only one `json.loads()` call used | Added second `json.loads()` after `isinstance(data, str)` check |
| `Invalid \escape` on responses with apostrophes | Strands writes span event content with `\'` (invalid JSON escape) | `.replace("\\'", "'")` in `_fix_escapes()` |
| 2nd+ call returned `b'"...'` literal | `BedrockAgentCoreClient` returns bytes chunks on 2nd+ call | `.decode("utf-8")` on all chunks |
| `@add_tracing` nested runs silently invisible | `@add_tracing` uses OTel; `mlflow.start_run(nested=True)` had no MLflow parent | Wrap with `DominoRun()` to create outer MLflow context |
| `@add_tracing` wrote to hidden experiment | Without `DominoRun()`, traces went to experiment 0 (internal, not user-visible) | Always wrap with `DominoRun()` |
| `DominoRun()` created new experiment per request | Each request = new execution context; `DominoRun()` without `experiment_name` creates a new one in production | Correct behavior; all land in `agent_experiment_{DOMINO_APP_ID}` — no fix needed |
| `DominoRun(experiment_name=...)` broke Performance tab | Overriding experiment prevented traces from reaching `agent_experiment_{DOMINO_APP_ID}` | Remove `experiment_name=` in production |
| Literal newlines in LLM response broke JSON parsing | Unescaped newlines inside JSON string values | Added `_try_parse()` with newline-escaping fallback |
| `\d` / `\w` / `\(` invalid JSON escape | LLM returns regex or math in code; `\X` where X is not a JSON escape char | `re.sub(r'\\(?!["\\\\/bfnrtu])', r'\\\\', s)` in `_fix_escapes()` |
| JSON parse still failing after fix | Mixed escape levels in multi-turn / complex responses | Added detailed error logging + `_regex_extract_response()` last-resort fallback (drops spans, always recovers response text) |
| `\n` disappearing from code examples in UI | `normalizeText()` in frontend re-decoded `\n` → newline on already-decoded data | Removed `\\n`/`\\t`/`\\"` replacements from `normalizeText()` |
| "Failed to fetch dataset details" in Performance tab | `DominoRun.__log_params()` called `create_external_model` with empty params (missing `agent_config.yaml`) | Added `agent_config.yaml`; pass `agent_config_path=` to `DominoRun()` |
| Token counts showed 0 in "Input/Output tokens (k)" columns | Built-in columns driven by `mlflow.chat.tokenUsage` span attribute; was using `log_evaluation` instead | Set `mlf.set_attribute("mlflow.chat.tokenUsage", {...})` inside `_replay_spans_as_mlflow_spans()` on LLM spans |
| Token counts doubled (2×) | Strands rolls up token totals to AGENT spans; flat replay → MLflow summed both LLM span and its AGENT parent | Only set `mlflow.chat.tokenUsage` on `SpanType.LLM` spans |
| `total_tokens` column didn't equal `input + output` | `log_evaluation("total_tokens")` summed all spans; `mlflow.chat.tokenUsage` only covered LLM spans | Filtered `log_evaluation` to same LLM-span subset |
| Markdown images rendered as broken links | marked v4 `cleanUrl()` returns `null` for some valid URLs | Custom `image()` renderer in `marked.use()` |
| Images blocked in Domino app | Domino nginx injects `Content-Security-Policy: img-src 'self'` | `_ImageCSPMiddleware` setting `img-src * data: blob:` |
| Links show "refused to connect" | App inside Domino iframe; external sites block iframe embedding | Custom `link()` renderer with `target="_blank" rel="noopener noreferrer"` |
