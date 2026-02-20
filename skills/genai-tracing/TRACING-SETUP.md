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

Enable auto-tracing for your LLM framework before making any calls:

### OpenAI

```python
import mlflow

# Enable OpenAI auto-tracing
mlflow.openai.autolog()

# Now all OpenAI calls are automatically traced
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic

```python
import mlflow

# Enable Anthropic auto-tracing
mlflow.anthropic.autolog()

# Now all Anthropic calls are automatically traced
from anthropic import Anthropic
client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### LangChain

```python
import mlflow

# Enable LangChain auto-tracing
mlflow.langchain.autolog()

# Now all LangChain operations are traced
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template("Tell me about {topic}")
chain = prompt | llm

response = chain.invoke({"topic": "machine learning"})
```

### Multiple Frameworks

```python
import mlflow

# Enable auto-tracing for multiple frameworks
mlflow.openai.autolog()
mlflow.anthropic.autolog()
mlflow.langchain.autolog()
```

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
from domino.agents.logging import DominoRun

@add_tracing(name="test_agent", autolog_frameworks=["openai"])
def test_agent(query: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content

with DominoRun() as run:
    result = test_agent("Say hello")
    print(f"Result: {result}")
    print(f"Run ID: {run.run_id}")
```

**Note:** The `autolog_frameworks` parameter in `@add_tracing` enables automatic tracing for the specified frameworks (e.g., `["openai"]`, `["langchain"]`, `["openai", "langchain"]`).

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

Recommended structure for GenAI projects:

```
my-agent-project/
├── agents/
│   ├── __init__.py
│   ├── classifier.py      # Classification agent
│   ├── responder.py       # Response generation agent
│   └── evaluators.py      # Custom evaluators
├── config/
│   └── config.yaml        # Agent configuration
├── main.py                # Entry point with DominoRun
├── requirements.txt
└── Dockerfile             # Custom environment
```

## Troubleshooting Setup

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

### Traces Not Appearing

1. Verify MLflow tracking URI is set (automatic in Domino)
2. Check experiment name matches expected format
3. Ensure `DominoRun` context manager is used
4. Verify auto-logging is enabled before LLM calls

### API Key Issues

```
openai.AuthenticationError: Incorrect API key provided
```

**Solution**: Set API keys in Domino environment variables, not in code.

## Next Steps

- [ADD-TRACING-DECORATOR.md](./ADD-TRACING-DECORATOR.md) - Learn about @add_tracing
- [DOMINO-RUN.md](./DOMINO-RUN.md) - Learn about DominoRun context
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - See complete example
