# GenAI Evaluators Guide

Evaluators are functions that score the outputs of traced functions. They enable quality measurement, comparison, and monitoring of GenAI applications.

## Evaluator Function Signature

```python
def evaluator(inputs: dict, output: Any) -> dict:
    """
    Args:
        inputs: Dictionary of argument names to values passed to the traced function
        output: Return value of the traced function

    Returns:
        Dictionary of metric names to numeric values
    """
    return {"metric_name": score}
```

## Basic Evaluators

### Simple Length-Based

```python
def length_evaluator(inputs, output):
    """Evaluate based on response length."""
    if isinstance(output, str):
        length = len(output)
    elif isinstance(output, dict):
        length = len(str(output))
    else:
        length = 0

    return {
        "response_length": length,
        "is_substantial": 1.0 if length > 100 else 0.0,
    }
```

### Keyword Presence

```python
def keyword_evaluator(inputs, output):
    """Check for important keywords in response."""
    keywords = ["machine learning", "neural network", "algorithm"]
    output_lower = str(output).lower()

    matches = sum(1 for kw in keywords if kw in output_lower)

    return {
        "keyword_count": matches,
        "keyword_coverage": matches / len(keywords),
    }
```

### Confidence Extraction

```python
def confidence_evaluator(inputs, output):
    """Extract confidence from structured output."""
    if isinstance(output, dict):
        confidence = output.get("confidence", 0)
        category = output.get("category", "unknown")
    else:
        confidence = 0
        category = "unknown"

    return {
        "confidence": confidence,
        "has_category": 1.0 if category != "unknown" else 0.0,
    }
```

## LLM-as-Judge Evaluators

### Basic LLM Judge

```python
from openai import OpenAI

client = OpenAI()

def llm_judge_evaluator(inputs, output):
    """Use GPT to evaluate response quality."""
    judge_prompt = f"""
    Rate the following response on a scale of 0-10.

    Question: {inputs.get('query', 'N/A')}
    Response: {output}

    Consider:
    - Relevance to the question
    - Completeness of answer
    - Clarity of explanation

    Respond with only a number 0-10.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": judge_prompt}],
        max_tokens=10,
        temperature=0.1,
    )

    try:
        score = float(response.choices[0].message.content.strip())
        score = max(0, min(10, score)) / 10  # Normalize to 0-1
    except:
        score = 0.5  # Default if parsing fails

    return {"llm_judge_score": score}
```

### Multi-Criteria LLM Judge

```python
import json

def multi_criteria_judge(inputs, output):
    """Evaluate multiple dimensions with LLM."""
    judge_prompt = f"""
    Evaluate this response on multiple criteria.

    Question: {inputs.get('query', 'N/A')}
    Response: {output}

    Rate each criterion 0-10:
    1. relevance: How relevant is the response to the question?
    2. completeness: How complete is the answer?
    3. accuracy: How accurate is the information?
    4. clarity: How clear is the explanation?

    Respond in JSON format:
    {{"relevance": X, "completeness": X, "accuracy": X, "clarity": X}}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": judge_prompt}],
        max_tokens=100,
        temperature=0.1,
    )

    try:
        scores = json.loads(response.choices[0].message.content)
        # Normalize to 0-1
        return {k: v / 10.0 for k, v in scores.items()}
    except:
        return {
            "relevance": 0.5,
            "completeness": 0.5,
            "accuracy": 0.5,
            "clarity": 0.5,
        }
```

### Pairwise Comparison Judge

```python
def pairwise_judge(inputs, output, baseline_output):
    """Compare output against a baseline."""
    judge_prompt = f"""
    Compare these two responses to the question.

    Question: {inputs.get('query', 'N/A')}

    Response A (Baseline): {baseline_output}
    Response B (New): {output}

    Which response is better? Consider relevance, completeness, and clarity.

    Respond with:
    - "A" if baseline is better
    - "B" if new is better
    - "TIE" if equal
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": judge_prompt}],
        max_tokens=10,
        temperature=0.1,
    )

    verdict = response.choices[0].message.content.strip().upper()

    return {
        "wins_vs_baseline": 1.0 if verdict == "B" else 0.0,
        "ties_vs_baseline": 1.0 if verdict == "TIE" else 0.0,
        "loses_vs_baseline": 1.0 if verdict == "A" else 0.0,
    }
```

## Domain-Specific Evaluators

### Classification Evaluator

```python
def classification_evaluator(inputs, output):
    """Evaluate classification results."""
    expected_categories = ["bug", "feature", "question", "other"]

    if isinstance(output, dict):
        category = output.get("category", "")
        confidence = output.get("confidence", 0)
    else:
        category = str(output)
        confidence = 0

    return {
        "is_valid_category": 1.0 if category in expected_categories else 0.0,
        "classification_confidence": confidence,
        "high_confidence": 1.0 if confidence > 0.8 else 0.0,
    }
```

### RAG Evaluator

```python
def rag_evaluator(inputs, output):
    """Evaluate RAG (Retrieval-Augmented Generation) responses."""
    query = inputs.get("query", "")
    context = inputs.get("context", "")

    if isinstance(output, dict):
        answer = output.get("answer", "")
        sources = output.get("sources", [])
    else:
        answer = str(output)
        sources = []

    # Check if answer uses context
    context_words = set(context.lower().split())
    answer_words = set(answer.lower().split())
    context_overlap = len(context_words & answer_words) / max(len(context_words), 1)

    return {
        "context_utilization": context_overlap,
        "source_count": len(sources),
        "has_sources": 1.0 if sources else 0.0,
        "answer_length": len(answer),
    }
```

### Safety Evaluator

```python
def safety_evaluator(inputs, output):
    """Check for safety issues in output."""
    output_str = str(output).lower()

    # Simple keyword-based safety check
    unsafe_patterns = [
        "i cannot", "i'm not able to", "harmful", "illegal",
        "violence", "hate", "discriminat"
    ]

    safety_flags = sum(1 for p in unsafe_patterns if p in output_str)

    return {
        "safety_flag_count": safety_flags,
        "is_safe": 1.0 if safety_flags == 0 else 0.0,
    }
```

## Composite Evaluators

### Combining Multiple Evaluators

```python
def composite_evaluator(inputs, output):
    """Combine multiple evaluation methods."""
    scores = {}

    # Length metrics
    scores.update(length_evaluator(inputs, output))

    # Safety metrics
    scores.update(safety_evaluator(inputs, output))

    # LLM judge metrics
    scores.update(llm_judge_evaluator(inputs, output))

    # Compute overall score
    scores["overall_score"] = (
        scores.get("llm_judge_score", 0) * 0.5 +
        scores.get("is_safe", 1) * 0.3 +
        min(scores.get("response_length", 0) / 500, 1.0) * 0.2
    )

    return scores
```

### Conditional Evaluator

```python
def conditional_evaluator(inputs, output):
    """Apply different evaluation based on input type."""
    query_type = inputs.get("query_type", "general")

    base_scores = {
        "response_length": len(str(output)),
    }

    if query_type == "classification":
        base_scores.update(classification_evaluator(inputs, output))
    elif query_type == "qa":
        base_scores.update(llm_judge_evaluator(inputs, output))
    elif query_type == "rag":
        base_scores.update(rag_evaluator(inputs, output))

    return base_scores
```

## Post-Hoc Evaluation

### Adding Evaluations to Existing Traces

```python
from domino.agents.tracing import search_traces, log_evaluation

def add_post_hoc_evaluations(run_id):
    """Add evaluations to traces after the fact."""
    # Retrieve traces from run
    traces = search_traces(run_id=run_id)

    for trace in traces.data:
        # Get trace inputs and outputs
        inputs = trace.inputs
        output = trace.outputs

        # Calculate new evaluation
        combined_score = calculate_combined_score(inputs, output)

        # Log evaluation to existing trace
        log_evaluation(
            trace_id=trace.id,
            name="combined_quality_score",
            value=round(combined_score, 2)
        )

# Usage after a run completes
add_post_hoc_evaluations(run_id="abc123")
```

### Human-in-the-Loop Evaluation

```python
from domino.agents.tracing import search_traces, log_evaluation

def collect_human_feedback(run_id):
    """Collect human feedback for traces."""
    traces = search_traces(run_id=run_id)

    for trace in traces.data:
        # Display to human reviewer
        print(f"Input: {trace.inputs}")
        print(f"Output: {trace.outputs}")

        # Collect feedback
        rating = input("Rate 1-5: ")

        # Log human evaluation
        log_evaluation(
            trace_id=trace.id,
            name="human_rating",
            value=float(rating) / 5.0
        )
```

## Evaluator Patterns

### Factory Pattern

```python
def create_threshold_evaluator(threshold: float):
    """Create evaluator with custom threshold."""
    def evaluator(inputs, output):
        confidence = output.get("confidence", 0) if isinstance(output, dict) else 0
        return {
            "meets_threshold": 1.0 if confidence >= threshold else 0.0,
            "confidence": confidence,
        }
    return evaluator

# Usage
high_confidence_evaluator = create_threshold_evaluator(0.9)
medium_confidence_evaluator = create_threshold_evaluator(0.7)

@add_tracing(name="agent", evaluator=high_confidence_evaluator)
def my_agent(query):
    pass
```

### Caching Pattern for Expensive Evaluations

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_llm_judge(query: str, output: str) -> float:
    """Cache LLM judge results to avoid redundant calls."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Rate 0-10: {query} -> {output}"}],
        max_tokens=10,
    )
    return float(response.choices[0].message.content.strip()) / 10

def efficient_evaluator(inputs, output):
    query = inputs.get("query", "")
    output_str = str(output)

    # Use cached evaluation
    score = cached_llm_judge(query, output_str)

    return {"quality_score": score}
```

## Best Practices

### 1. Return Consistent Metrics

```python
# Good: Always return same metrics
def consistent_evaluator(inputs, output):
    return {
        "quality": calculate_quality(output),
        "relevance": calculate_relevance(inputs, output),
    }

# Bad: Different metrics based on condition
def inconsistent_evaluator(inputs, output):
    if condition:
        return {"quality": 1.0}
    else:
        return {"relevance": 0.5}  # Different metric!
```

### 2. Handle Edge Cases

```python
def robust_evaluator(inputs, output):
    try:
        if output is None:
            return {"quality": 0.0, "error": 1.0}

        if isinstance(output, dict):
            text = output.get("response", "")
        else:
            text = str(output)

        return {
            "quality": calculate_quality(text),
            "error": 0.0,
        }
    except Exception as e:
        return {"quality": 0.0, "error": 1.0}
```

### 3. Keep Evaluators Fast

```python
# Good: Fast local evaluation
def fast_evaluator(inputs, output):
    return {"length": len(str(output))}

# Use sparingly: Slow LLM evaluation
def slow_evaluator(inputs, output):
    # Only for critical metrics
    return {"llm_score": expensive_llm_call(output)}
```

### 4. Document Expected Metrics

```python
def documented_evaluator(inputs, output):
    """
    Evaluates agent responses.

    Returns:
        quality_score (float): 0-1 overall quality
        relevance (float): 0-1 relevance to query
        completeness (float): 0-1 answer completeness
        is_safe (float): 1.0 if safe, 0.0 if unsafe
    """
    return {
        "quality_score": ...,
        "relevance": ...,
        "completeness": ...,
        "is_safe": ...,
    }
```

## Next Steps

- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - See evaluators in action
