# @add_tracing Decorator Guide

The `@add_tracing` decorator is the core mechanism for capturing traces in Domino GenAI applications.

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

## Decorator Parameters

### name (required)

The trace name shown in the UI:

```python
@add_tracing(name="incident_classifier")
def classify_incident(incident: dict) -> dict:
    pass
```

### evaluator (optional)

Function to evaluate the output:

```python
def my_evaluator(inputs, output):
    return {"quality_score": calculate_score(output)}

@add_tracing(name="my_agent", evaluator=my_evaluator)
def my_agent(query: str) -> str:
    pass
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

### Nested LLM Calls

With auto-logging enabled, all LLM calls within the function are captured as child spans:

```python
import mlflow
from domino.agents.tracing import add_tracing
from openai import OpenAI

mlflow.openai.autolog()
client = OpenAI()

@add_tracing(name="multi_step_agent")
def multi_step_agent(query: str) -> str:
    # First LLM call - captured as child span
    classification = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Classify: {query}"}]
    )

    # Second LLM call - captured as child span
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Respond to: {query}"}]
    )

    return response.choices[0].message.content
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

## With Evaluators

### Basic Evaluator

```python
def quality_evaluator(inputs, output):
    """
    Evaluator function signature:
    - inputs: dict of argument names to values
    - output: return value of the decorated function

    Returns: dict of metric names to values
    """
    score = len(output) / 100  # Simple length-based score
    return {"quality_score": min(score, 1.0)}

@add_tracing(name="my_agent", evaluator=quality_evaluator)
def my_agent(query: str) -> str:
    return llm.invoke(query)
```

### LLM-as-Judge Evaluator

```python
def llm_judge_evaluator(inputs, output):
    """Use a separate LLM to evaluate quality."""
    judge_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""Rate this response 0-10:
            Question: {inputs['query']}
            Response: {output}
            Score (just the number):"""
        }]
    )
    score = float(judge_response.choices[0].message.content.strip()) / 10
    return {"judge_score": score}

@add_tracing(name="evaluated_agent", evaluator=llm_judge_evaluator)
def evaluated_agent(query: str) -> str:
    return llm.invoke(query)
```

### Multi-Metric Evaluator

```python
def comprehensive_evaluator(inputs, output):
    return {
        "relevance": assess_relevance(inputs["query"], output),
        "completeness": assess_completeness(output),
        "factuality": assess_factuality(output),
        "safety": assess_safety(output),
    }

@add_tracing(name="comprehensive_agent", evaluator=comprehensive_evaluator)
def comprehensive_agent(query: str) -> str:
    return llm.invoke(query)
```

## Async Functions

Tracing works with async functions:

```python
import asyncio
from domino.agents.tracing import add_tracing

@add_tracing(name="async_agent")
async def async_agent(query: str) -> str:
    response = await async_llm.invoke(query)
    return response

# Usage
async def main():
    result = await async_agent("Hello")
```

## Class Methods

Tracing works with class methods:

```python
class MyAgent:
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI()

    @add_tracing(name="agent_process")
    def process(self, query: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}]
        )
        return response.choices[0].message.content

# Usage
agent = MyAgent("gpt-4o-mini")
result = agent.process("Hello")
```

## Best Practices

### 1. Use Descriptive Names

```python
# Good
@add_tracing(name="incident_classification_agent")
@add_tracing(name="customer_response_generator")

# Bad
@add_tracing(name="agent1")
@add_tracing(name="process")
```

### 2. Return Structured Data

```python
@add_tracing(name="classifier")
def classify(text: str) -> dict:
    # Return dict for better trace visibility
    return {
        "category": "technical",
        "confidence": 0.95,
        "subcategories": ["api", "authentication"]
    }
```

### 3. Include Context in Evaluators

```python
def contextual_evaluator(inputs, output):
    # Access all inputs for context
    query = inputs.get("query", "")
    context = inputs.get("context", "")

    return {
        "relevance_to_query": assess_relevance(query, output),
        "used_context": context in output,
    }
```

### 4. Handle Errors Gracefully

```python
@add_tracing(name="safe_agent")
def safe_agent(query: str) -> dict:
    try:
        result = llm.invoke(query)
        return {"success": True, "result": result}
    except Exception as e:
        # Error is captured in trace
        return {"success": False, "error": str(e)}
```

## Next Steps

- [DOMINO-RUN.md](./DOMINO-RUN.md) - Group traces with DominoRun
- [EVALUATORS.md](./EVALUATORS.md) - Advanced evaluator patterns
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - Complete example
