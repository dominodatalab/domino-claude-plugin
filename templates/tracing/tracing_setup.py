"""
Domino GenAI Tracing Setup

This module provides utilities for setting up GenAI tracing in Domino
using the @add_tracing decorator and DominoRun context manager.

Requirements:
    - mlflow==3.2.0
    - dominodatalab[data,aisystems] @ git+https://github.com/dominodatalab/python-domino.git@master

Usage:
    from tracing_setup import setup_tracing, create_evaluator
    from domino.agents.tracing import add_tracing
    from domino.agents.logging import DominoRun

    setup_tracing("openai")

    @add_tracing(name="my_agent", evaluator=create_evaluator())
    def my_agent(query):
        return llm.invoke(query)

    with DominoRun(agent_config_path="config.yaml") as run:
        result = my_agent("Hello")
"""

import mlflow
import os


def setup_tracing(framework: str = "openai"):
    """
    Enable auto-tracing for LLM framework.

    Args:
        framework: One of 'openai', 'anthropic', 'langchain'

    Raises:
        ValueError: If unknown framework specified
    """
    if framework == "openai":
        mlflow.openai.autolog()
        print("Enabled OpenAI auto-tracing")
    elif framework == "anthropic":
        mlflow.anthropic.autolog()
        print("Enabled Anthropic auto-tracing")
    elif framework == "langchain":
        mlflow.langchain.autolog()
        print("Enabled LangChain auto-tracing")
    else:
        raise ValueError(f"Unknown framework: {framework}. Use 'openai', 'anthropic', or 'langchain'")


def create_evaluator(metrics: list = None):
    """
    Create a basic evaluator function for @add_tracing.

    Args:
        metrics: List of metric names to include (default: quality_score, response_length)

    Returns:
        Evaluator function compatible with @add_tracing decorator
    """
    if metrics is None:
        metrics = ["quality_score", "response_length"]

    def evaluator(inputs, output):
        """
        Evaluate agent output.

        Args:
            inputs: Dict of argument names to values passed to traced function
            output: Return value of the traced function

        Returns:
            Dict of metric names to numeric values
        """
        scores = {}

        # Calculate response length
        if "response_length" in metrics:
            if isinstance(output, str):
                scores["response_length"] = len(output)
            elif isinstance(output, dict):
                response = output.get("response", output.get("content", str(output)))
                scores["response_length"] = len(str(response))
            else:
                scores["response_length"] = len(str(output))

        # Placeholder quality score (replace with actual evaluation)
        if "quality_score" in metrics:
            scores["quality_score"] = 0.8

        # Extract confidence if available
        if "confidence" in metrics and isinstance(output, dict):
            scores["confidence"] = output.get("confidence", 0)

        return scores

    return evaluator


def create_llm_judge_evaluator(judge_model: str = "gpt-4o-mini"):
    """
    Create an LLM-as-judge evaluator.

    Args:
        judge_model: Model to use for evaluation

    Returns:
        Evaluator function that uses LLM to score responses
    """
    def evaluator(inputs, output):
        """Use LLM to evaluate response quality."""
        from openai import OpenAI

        client = OpenAI()

        # Extract query and response
        query = inputs.get("query", inputs.get("question", str(inputs)))
        if isinstance(output, dict):
            response = output.get("response", output.get("content", str(output)))
        else:
            response = str(output)

        judge_prompt = f"""Rate this response on a scale of 0-10.

Question: {query}
Response: {response}

Consider:
- Relevance: Does it answer the question?
- Completeness: Is the answer thorough?
- Clarity: Is it easy to understand?

Respond with only a number 0-10."""

        try:
            judge_response = client.chat.completions.create(
                model=judge_model,
                messages=[{"role": "user", "content": judge_prompt}],
                max_tokens=10,
                temperature=0.1,
            )
            score = float(judge_response.choices[0].message.content.strip())
            score = max(0, min(10, score)) / 10  # Normalize to 0-1
        except Exception:
            score = 0.5  # Default if evaluation fails

        return {
            "llm_judge_score": score,
            "judge_model": judge_model,
        }

    return evaluator


def get_aggregation_metrics(metric_names: list = None):
    """
    Get default aggregation metrics for DominoRun.

    Args:
        metric_names: List of metric names to aggregate

    Returns:
        List of (metric_name, aggregation_type) tuples
    """
    if metric_names is None:
        metric_names = ["quality_score", "response_length", "confidence"]

    aggregations = []
    for name in metric_names:
        aggregations.append((name, "mean"))
        if name in ["response_length", "latency"]:
            aggregations.append((name, "max"))
        if name in ["quality_score", "confidence"]:
            aggregations.append((name, "min"))

    return aggregations


# Example usage
if __name__ == "__main__":
    from domino.agents.tracing import add_tracing
    from domino.agents.logging import DominoRun
    from openai import OpenAI

    # Setup
    setup_tracing("openai")
    client = OpenAI()

    # Create evaluator
    evaluator = create_evaluator(["quality_score", "response_length"])

    @add_tracing(name="example_agent", evaluator=evaluator)
    def example_agent(query: str) -> dict:
        """Example traced agent."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}]
        )
        return {
            "response": response.choices[0].message.content,
            "model": "gpt-4o-mini",
        }

    # Run with tracing
    aggregated_metrics = get_aggregation_metrics(["quality_score", "response_length"])

    with DominoRun(
        run_name="example-tracing-run",
        custom_summary_metrics=aggregated_metrics
    ) as run:
        result = example_agent("What is machine learning?")
        print(f"Response: {result['response'][:100]}...")
        print(f"Run ID: {run.run_id}")
