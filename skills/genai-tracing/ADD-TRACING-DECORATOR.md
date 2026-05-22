# @add_tracing Decorator Guide

The `@add_tracing` decorator is the core mechanism for capturing traces in Domino GenAI applications.

**Important:** `@add_tracing` creates traces independently — it does NOT require a `DominoRun` wrapper. In deployed Domino Apps, calling `@add_tracing`-decorated functions without `DominoRun` routes traces to the App Performance tab. Wrapping in `DominoRun` redirects them to the Experiments UI instead.

## Decorator Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Trace name shown in the UI |
| `span_type` | No | Span classification for the trace tree. Values: `"AGENT"`, `"TOOL"`, `"LLM"`, `"CHAIN"`. Use `"AGENT"` for the top-level agent function. |
| `autolog_frameworks` | No | List of LLM frameworks to auto-trace within this function's scope: `["openai"]`, `["anthropic"]`, `["openai", "anthropic"]` |
| `evaluator` | No | Function to score the output (see [EVALUATORS.md](./EVALUATORS.md)) |

## Basic Usage

### Simple Tracing

```python
from domino.agents.tracing import add_tracing

@add_tracing(name="my_agent_function")
def my_agent_function(query: str) -> str:
    """
    The @add_tracing decorator captures:
    - Function inputs (arguments)
    - Function output (return value)
    - Execution time
    - Any LLM calls made within (if auto-logging enabled)
    - Errors and exceptions
    """
    response = llm.invoke(query)
    return response
```

### With span_type and autolog_frameworks

```python
@add_tracing(
    name="agent_turn",
    span_type="AGENT",
    autolog_frameworks=["openai", "anthropic"],
)
async def run_agent_turn(messages: list[dict]) -> dict:
    """
    span_type="AGENT" classifies this as the top-level agent span in the trace tree.
    autolog_frameworks captures all OpenAI and Anthropic SDK calls as child spans.
    """
    response = await create_message(model="gpt-4o", messages=messages)
    return {"content": response}
```

### With LLM Framework

```python
import mlflow
from domino.agents.tracing import add_tracing
from openai import OpenAI

# Enable auto-tracing for OpenAI
mlflow.openai.autolog()

client = OpenAI()

@add_tracing(name="chat_agent")
def chat_agent(user_message: str) -> str:
    """All OpenAI calls within are automatically traced."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_message}]
    )
    return response.choices[0].message.content
```

## Manual Spans with mlflow.start_span()

For dynamic operations like tool-use agent loops where the function name isn't known at decoration time, use `mlflow.start_span()` to create child spans inside an `@add_tracing`-decorated function.

### Tool Call Spans

```python
import mlflow

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call wrapped in an MLflow child span."""
    with mlflow.start_span(name=f"tool:{tool_name}", span_type="TOOL") as span:
        span.set_inputs({"tool": tool_name, "input": tool_input})
        try:
            result = await dispatch_tool(tool_name, tool_input)
            span.set_outputs({"result": result[:500]})
            return result
        except Exception as e:
            span.set_outputs({"error": str(e)})
            raise
```

### LLM Call Spans

```python
import mlflow

async def call_llm(model: str, messages: list, max_tokens: int) -> dict:
    """Wrap each LLM SDK call in a span for explicit token/latency capture."""
    with mlflow.start_span(name="llm_call", span_type="LLM") as span:
        span.set_inputs({"model": model, "path": "gateway", "max_tokens": max_tokens})
        response = await client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens,
        )
        usage = response.usage
        span.set_outputs({
            "finish_reason": response.choices[0].finish_reason,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        })
    return response
```

### Complete Tool-Use Agent Pattern

This is the most common agentic pattern — an `@add_tracing`-decorated agent function with `mlflow.start_span` for tool and LLM calls:

```python
import mlflow
from domino.agents.tracing import add_tracing

@add_tracing(
    name="agent_turn",
    span_type="AGENT",
    autolog_frameworks=["openai", "anthropic"],
)
async def run_agent(messages: list[dict], context: str) -> dict:
    """Full agent loop with nested LLM and TOOL spans."""
    try:
        mlflow.update_current_trace(
            tags={"session_id": "abc", "actor": "agent"}
        )
    except Exception:
        pass

    working_messages = [m.copy() for m in messages]
    tool_calls_made = []
    total_input_tokens = 0
    total_output_tokens = 0

    for iteration in range(8):
        # LLM call with explicit span
        with mlflow.start_span(name="llm_call", span_type="LLM") as span:
            span.set_inputs({"model": "gpt-4o", "iteration": iteration})
            response = await client.chat.completions.create(
                model="gpt-4o", messages=working_messages, tools=TOOLS,
            )
            span.set_outputs({
                "finish_reason": response.choices[0].finish_reason,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            })
        total_input_tokens += response.usage.prompt_tokens
        total_output_tokens += response.usage.completion_tokens

        if response.choices[0].finish_reason != "tool_calls":
            # Final response — annotate the outer AGENT span
            _annotate_active_span({
                "tool_calls": len(tool_calls_made),
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
            })
            return {"content": response.choices[0].message.content, "tool_calls_made": tool_calls_made}

        # Execute tool calls with TOOL spans
        for tc in response.choices[0].message.tool_calls:
            with mlflow.start_span(name=f"tool:{tc.function.name}", span_type="TOOL") as span:
                span.set_inputs({"tool": tc.function.name, "input": tc.function.arguments})
                result = await dispatch_tool(tc.function.name, tc.function.arguments)
                span.set_outputs({"result": result[:500]})
                tool_calls_made.append({"name": tc.function.name, "output": result})

        # Continue conversation with tool results
        working_messages.append({"role": "assistant", "content": None, "tool_calls": response.choices[0].message.tool_calls})
        for tc, result in zip(response.choices[0].message.tool_calls, [t["output"] for t in tool_calls_made[-len(response.choices[0].message.tool_calls):]]):
            working_messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return {"content": "Max iterations reached.", "tool_calls_made": tool_calls_made}


def _annotate_active_span(attrs: dict) -> None:
    """Safely set attributes on the current MLflow span."""
    try:
        span = mlflow.get_current_active_span()
        if span is not None:
            for k, v in attrs.items():
                span.set_attribute(k, v)
    except Exception:
        pass
```

The resulting trace tree in the UI:

```
agent_turn (AGENT)
├── llm_call (LLM) — first model call
├── tool:get_data (TOOL) — tool execution
├── tool:analyze (TOOL) — tool execution
├── llm_call (LLM) — second model call with tool results
```

## Span Annotation APIs

Attach metadata to traces and spans for filtering and debugging.

### Trace-Level Tags

```python
# Tag the entire trace (visible in trace list, used for filtering)
mlflow.update_current_trace(
    tags={"session_id": "abc123", "actor": "agent", "installation": "NS_NORFOLK"}
)
```

### Span-Level Attributes

```python
# Annotate the current span with metrics
span = mlflow.get_current_active_span()
if span is not None:
    span.set_attribute("tool_calls", 5)
    span.set_attribute("total_input_tokens", 12000)
    span.set_attribute("total_output_tokens", 850)
    span.set_attribute("model", "gpt-4o")
```

## What Gets Captured

### Inputs

All function arguments are captured:

```python
@add_tracing(name="process_data")
def process_data(text: str, max_length: int = 100, options: dict = None):
    pass

# Trace captures: text, max_length, options
```

### Outputs

The return value is captured:

```python
@add_tracing(name="generate_response")
def generate_response(query: str) -> dict:
    return {
        "answer": "...",
        "confidence": 0.95,
        "sources": ["doc1", "doc2"]
    }

# Trace captures the entire return dict
```

### Errors and Exceptions

Exceptions are captured in the trace:

```python
@add_tracing(name="risky_operation")
def risky_operation(data: dict) -> str:
    if not data:
        raise ValueError("Data cannot be empty")  # Captured in trace
    return process(data)
```

## Nested Tracing

Chain multiple traced functions for hierarchical traces:

```python
@add_tracing(name="classifier")
def classify(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Classify: {text}"}]
    )
    return response.choices[0].message.content

@add_tracing(name="responder")
def respond(text: str, category: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Respond as {category}: {text}"}]
    )
    return response.choices[0].message.content

@add_tracing(name="pipeline")
def pipeline(text: str) -> dict:
    # Both nested calls appear as child spans
    category = classify(text)
    response = respond(text, category)
    return {"category": category, "response": response}
```

Trace hierarchy in UI:
```
pipeline
├── classifier
│   └── [OpenAI call]
└── responder
    └── [OpenAI call]
```

## Async Functions

Tracing works with async functions:

```python
import asyncio
from domino.agents.tracing import add_tracing

@add_tracing(name="async_agent", span_type="AGENT", autolog_frameworks=["openai"])
async def async_agent(query: str) -> str:
    response = await async_llm.invoke(query)
    return response

# Usage
async def main():
    result = await async_agent("Hello")
```

## Graceful Fallback (SDK Not Installed)

Always guard the import so your code works in environments without the Domino SDK:

```python
try:
    from domino.agents.tracing import add_tracing
    _HAS_DOMINO_SDK = True
except ImportError:
    _HAS_DOMINO_SDK = False
    def add_tracing(*_a, **_kw):
        def deco(fn):
            return fn
        return deco
```

## Best Practices

### 1. Use `@add_tracing` Only on Agent Entry Points

Put `@add_tracing` on the top-level agent orchestration function, not on every utility function. Use `mlflow.start_span()` for child operations.

```python
# Good: @add_tracing on the agent, mlflow.start_span for tools/LLM calls
@add_tracing(name="agent_turn", span_type="AGENT")
async def run_agent(messages):
    with mlflow.start_span(name="llm_call", span_type="LLM"):
        ...
    with mlflow.start_span(name="tool:search", span_type="TOOL"):
        ...

# Bad: @add_tracing on every function
@add_tracing(name="search_tool")  # Don't do this
def search(query):
    ...
```

### 2. Use Descriptive Names

```python
# Good
@add_tracing(name="incident_classification_agent", span_type="AGENT")
@add_tracing(name="customer_response_generator", span_type="AGENT")

# Bad
@add_tracing(name="agent1")
@add_tracing(name="process")
```

### 3. Always Set span_type for Agent Functions

```python
@add_tracing(name="my_agent", span_type="AGENT", autolog_frameworks=["openai"])
```

### 4. Return Structured Data

```python
@add_tracing(name="classifier", span_type="AGENT")
def classify(text: str) -> dict:
    # Return dict for better trace visibility
    return {
        "category": "technical",
        "confidence": 0.95,
        "subcategories": ["api", "authentication"]
    }
```

## Next Steps

- [DOMINO-RUN.md](./DOMINO-RUN.md) - Group traces with DominoRun (development/evaluation only)
- [EVALUATORS.md](./EVALUATORS.md) - Advanced evaluator patterns
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - Complete example
