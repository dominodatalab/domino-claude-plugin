# GenAI Tracing Setup for Domino

This guide covers setting up the environment and SDK for GenAI tracing in Domino Data Lab.

## Environment Requirements

### Compute Environment Setup

**IMPORTANT**: Domino Standard Environments (DSEs) include an older MLflow version. You must create a custom environment with MLflow 3.2.0 for GenAI tracing.

Add to your Dockerfile:

```dockerfile
USER root

# Install MLflow 3.2.0 (required for GenAI tracing)
RUN pip install mlflow==3.2.0

# Install Domino SDK with AI systems support
RUN pip install --no-cache-dir "git+https://github.com/dominodatalab/python-domino.git@master#egg=dominodatalab[data,aisystems]"

# Install your LLM framework (choose one or more)
RUN pip install openai>=1.0.0
RUN pip install anthropic>=0.18.0
RUN pip install langchain>=0.1.0

USER ubuntu
```

### Requirements File Alternative

```text
# requirements.txt
mlflow==3.2.0
dominodatalab[data,aisystems] @ git+https://github.com/dominodatalab/python-domino.git@master
openai>=1.0.0
anthropic>=0.18.0
langchain>=0.1.0
```

## Framework Auto-Logging

Enable auto-tracing for your LLM framework before making any calls. **Each framework should be in its own try/except** so one failure doesn't block the others:

```python
import mlflow

# Each autolog in its own try/except
try:
    mlflow.openai.autolog()
except Exception:
    pass
try:
    mlflow.anthropic.autolog()
except Exception:
    pass
try:
    mlflow.langchain.autolog()
except Exception:
    pass
```

### Where to Call autolog

**Deployed Apps (FastAPI/Flask):** In the app lifespan, before any requests are handled:

```python
import mlflow
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enable autolog — NO mlflow.set_experiment() for deployed apps
    try:
        mlflow.openai.autolog()
    except Exception:
        pass
    try:
        mlflow.anthropic.autolog()
    except Exception:
        pass
    yield

app = FastAPI(lifespan=lifespan)
```

**Batch scripts / Jobs:** At the top of your script, before any LLM calls:

```python
import mlflow

mlflow.openai.autolog()
mlflow.anthropic.autolog()
```

### Important: Do NOT Call mlflow.set_experiment() in Deployed Apps

Domino auto-creates an experiment named `agent_experiment_{app_id}` for each deployed App. The App Performance tab reads traces from this experiment. If you call `mlflow.set_experiment("my-custom-name")`, traces are redirected to your custom experiment and the Performance tab won't see them.

```python
# BAD — deployed app, overrides auto-routing
mlflow.set_experiment("my-agent-experiment")  # Performance tab won't see traces

# GOOD — deployed app, let Domino handle routing
# Just call autolog, nothing else
```

For development/evaluation scripts, `mlflow.set_experiment()` is fine — traces go to the Experiments UI.

## Verifying Setup

### Check MLflow Version

```python
import mlflow
print(f"MLflow version: {mlflow.__version__}")
# Should print: MLflow version: 3.2.0
```

### Check Domino SDK

```python
from domino.agents.tracing import add_tracing
from domino.agents.logging import DominoRun
print("Domino SDK with agents support installed successfully")
```

### Test Basic Tracing

```python
from domino.agents.tracing import add_tracing

@add_tracing(name="test_agent", span_type="AGENT", autolog_frameworks=["openai"])
def test_agent(query: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content

# @add_tracing creates the trace — no DominoRun needed
result = test_agent("Say hello")
print(f"Result: {result}")
```

## Environment Variables

### API Keys

Store API keys as Domino environment variables (never in code):

```python
import os

# Access in your code
openai_key = os.environ.get("OPENAI_API_KEY")
anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
```

### Domino-Provided Variables

These are automatically available:

| Variable | Description |
|----------|-------------|
| `DOMINO_STARTING_USERNAME` | User who started the run |
| `DOMINO_PROJECT_NAME` | Current project name |
| `DOMINO_RUN_ID` | Domino job run ID |
| `MLFLOW_TRACKING_URI` | MLflow tracking server URL |

## Project Structure

### Deployed App (FastAPI)

```
my-agent-app/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, lifespan with autolog (NO set_experiment)
│   │   ├── agent/
│   │   │   ├── orchestrator.py # @add_tracing on agent function, mlflow.start_span for tools/LLM
│   │   │   ├── llm_client.py   # LLM calls wrapped in mlflow.start_span(span_type="LLM")
│   │   │   └── tools.py        # Tool implementations (no tracing decorators)
│   │   └── routers/
│   │       └── agent.py        # Route handler — calls traced function directly, NO DominoRun
│   └── requirements.txt
├── frontend/
└── app.sh                      # Domino App entry point
```

### Batch Evaluation Script

```
my-agent-project/
├── agents/
│   ├── __init__.py
│   ├── classifier.py      # @add_tracing on agent functions
│   ├── responder.py
│   └── evaluators.py      # Custom evaluators
├── config/
│   └── config.yaml        # Agent configuration
├── main.py                # Entry point with DominoRun
├── requirements.txt
└── Dockerfile             # Custom environment
```

## Troubleshooting

### Traces Not Appearing in App Performance Tab

1. **Remove `mlflow.set_experiment()`** — it overrides Domino's auto-routing to `agent_experiment_{app_id}`
2. **Remove `DominoRun()` wrappers** — they redirect traces to the Experiments UI
3. **Ensure `@add_tracing` is on the agent function** — this is what creates the trace
4. **Check that autolog is enabled** — call `mlflow.openai.autolog()` / `mlflow.anthropic.autolog()` in the app lifespan
5. **Verify MLflow 3.2.0** — older versions don't support GenAI tracing

### Traces Not Appearing in Experiments UI

1. Verify MLflow tracking URI is set (automatic in Domino)
2. Ensure `DominoRun` context manager is used (required for Experiments UI)
3. Check experiment name matches expected format
4. Verify auto-logging is enabled before LLM calls

### MLflow Version Mismatch

```
Error: module 'mlflow' has no attribute 'openai'
```

**Solution**: Upgrade MLflow to 3.2.0:
```bash
pip install mlflow==3.2.0
```

### Domino SDK Import Error

```
ModuleNotFoundError: No module named 'domino.agents'
```

**Solution**: Install Domino SDK with AI systems support:
```bash
pip install --no-cache-dir "git+https://github.com/dominodatalab/python-domino.git@master#egg=dominodatalab[data,aisystems]"
```

### API Key Issues

```
openai.AuthenticationError: Incorrect API key provided
```

**Solution**: Set API keys in Domino environment variables, not in code.

## Next Steps

- [ADD-TRACING-DECORATOR.md](./ADD-TRACING-DECORATOR.md) - Learn about @add_tracing, span_type, mlflow.start_span
- [DOMINO-RUN.md](./DOMINO-RUN.md) - Learn about DominoRun context (development/evaluation only)
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - See complete example
