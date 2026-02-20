# Multi-Agent Tracing Example

This is a complete, production-ready example of a multi-agent system with full tracing, based on the Domino GenAI Tracing Blueprint.

## Incident Triage System Overview

This example implements an incident triage system with four specialized agents:

1. **Classifier Agent** - Categorizes incidents and assigns urgency
2. **Impact Agent** - Assesses blast radius and affected users
3. **Resource Agent** - Matches available responders based on skills
4. **Response Agent** - Drafts communications for stakeholders

## Project Structure

```
incident-triage/
├── agents/
│   ├── __init__.py
│   ├── classifier.py
│   ├── impact.py
│   ├── resource.py
│   └── response.py
├── evaluators/
│   ├── __init__.py
│   └── pipeline_evaluator.py
├── config.yaml
├── main.py
└── requirements.txt
```

## Configuration

### config.yaml

```yaml
models:
  primary: gpt-4o-mini
  fallback: gpt-3.5-turbo

agents:
  classifier:
    temperature: 0.3
    max_tokens: 500
    categories:
      - security
      - infrastructure
      - application
      - data
      - network
    urgency_levels:
      - critical
      - high
      - medium
      - low

  impact:
    temperature: 0.3
    max_tokens: 800

  resource:
    temperature: 0.5
    max_tokens: 600

  response:
    temperature: 0.7
    max_tokens: 1500

settings:
  retry_count: 3
  timeout_seconds: 30
```

## Agent Implementations

### agents/classifier.py

```python
import mlflow
from domino.agents.tracing import add_tracing
from openai import OpenAI
import yaml

mlflow.openai.autolog()
client = OpenAI()

with open("config.yaml") as f:
    config = yaml.safe_load(f)

def classifier_evaluator(inputs, output):
    """Evaluate classification quality."""
    valid_categories = config["agents"]["classifier"]["categories"]
    valid_urgencies = config["agents"]["classifier"]["urgency_levels"]

    category = output.get("category", "")
    urgency = output.get("urgency", "")
    confidence = output.get("confidence", 0)

    return {
        "classification_confidence": confidence,
        "valid_category": 1.0 if category in valid_categories else 0.0,
        "valid_urgency": 1.0 if urgency in valid_urgencies else 0.0,
        "high_confidence": 1.0 if confidence > 0.8 else 0.0,
    }

@add_tracing(name="classifier_agent", evaluator=classifier_evaluator)
def classify_incident(incident: dict) -> dict:
    """
    Categorize incident and assign urgency level.

    Args:
        incident: Dict with 'title', 'description', 'source'

    Returns:
        Dict with 'category', 'urgency', 'confidence', 'reasoning'
    """
    categories = config["agents"]["classifier"]["categories"]
    urgencies = config["agents"]["classifier"]["urgency_levels"]

    prompt = f"""
    Classify this incident:

    Title: {incident.get('title', 'N/A')}
    Description: {incident.get('description', 'N/A')}
    Source: {incident.get('source', 'N/A')}

    Categories: {', '.join(categories)}
    Urgency Levels: {', '.join(urgencies)}

    Respond in JSON format:
    {{
        "category": "<category>",
        "urgency": "<urgency>",
        "confidence": <0.0-1.0>,
        "reasoning": "<brief explanation>"
    }}
    """

    response = client.chat.completions.create(
        model=config["models"]["primary"],
        messages=[{"role": "user", "content": prompt}],
        temperature=config["agents"]["classifier"]["temperature"],
        max_tokens=config["agents"]["classifier"]["max_tokens"],
    )

    import json
    result = json.loads(response.choices[0].message.content)
    return result
```

### agents/impact.py

```python
import mlflow
from domino.agents.tracing import add_tracing
from openai import OpenAI
import yaml
import json

mlflow.openai.autolog()
client = OpenAI()

with open("config.yaml") as f:
    config = yaml.safe_load(f)

def impact_evaluator(inputs, output):
    """Evaluate impact assessment quality."""
    return {
        "impact_score": output.get("score", 0),
        "has_affected_users": 1.0 if output.get("affected_users", 0) > 0 else 0.0,
        "has_financial_estimate": 1.0 if output.get("financial_exposure") else 0.0,
    }

@add_tracing(name="impact_agent", evaluator=impact_evaluator)
def assess_impact(incident: dict, classification: dict) -> dict:
    """
    Evaluate blast radius, affected users, financial exposure.

    Args:
        incident: Original incident data
        classification: Output from classifier agent

    Returns:
        Dict with 'score', 'affected_users', 'affected_systems',
        'financial_exposure', 'reasoning'
    """
    prompt = f"""
    Assess the impact of this {classification['category']} incident:

    Title: {incident.get('title', 'N/A')}
    Description: {incident.get('description', 'N/A')}
    Urgency: {classification['urgency']}

    Estimate:
    1. Impact score (0-10)
    2. Number of affected users
    3. Affected systems
    4. Potential financial exposure

    Respond in JSON format:
    {{
        "score": <0-10>,
        "affected_users": <number>,
        "affected_systems": ["<system1>", "<system2>"],
        "financial_exposure": "<estimate or 'unknown'>",
        "reasoning": "<brief explanation>"
    }}
    """

    response = client.chat.completions.create(
        model=config["models"]["primary"],
        messages=[{"role": "user", "content": prompt}],
        temperature=config["agents"]["impact"]["temperature"],
        max_tokens=config["agents"]["impact"]["max_tokens"],
    )

    result = json.loads(response.choices[0].message.content)
    return result
```

### agents/resource.py

```python
import mlflow
from domino.agents.tracing import add_tracing
from openai import OpenAI
import yaml
import json

mlflow.openai.autolog()
client = OpenAI()

with open("config.yaml") as f:
    config = yaml.safe_load(f)

def resource_evaluator(inputs, output):
    """Evaluate resource matching quality."""
    return {
        "responder_count": len(output.get("responders", [])),
        "has_eta": 1.0 if output.get("eta") else 0.0,
        "meets_sla": 1.0 if output.get("meets_sla", False) else 0.0,
    }

@add_tracing(name="resource_agent", evaluator=resource_evaluator)
def match_resources(
    incident: dict,
    classification: dict,
    impact: dict
) -> dict:
    """
    Identify available responders based on skills and SLA.

    Args:
        incident: Original incident data
        classification: Output from classifier agent
        impact: Output from impact agent

    Returns:
        Dict with 'responders', 'eta', 'meets_sla', 'escalation_path'
    """
    prompt = f"""
    Find appropriate responders for this incident:

    Category: {classification['category']}
    Urgency: {classification['urgency']}
    Impact Score: {impact['score']}
    Affected Systems: {impact.get('affected_systems', [])}

    Determine:
    1. Required skills
    2. Recommended responders (by role)
    3. Estimated time to respond
    4. Escalation path if needed

    Respond in JSON format:
    {{
        "required_skills": ["<skill1>", "<skill2>"],
        "responders": [
            {{"role": "<role>", "priority": <1-3>}}
        ],
        "eta": "<time estimate>",
        "meets_sla": <true/false>,
        "escalation_path": ["<level1>", "<level2>"]
    }}
    """

    response = client.chat.completions.create(
        model=config["models"]["primary"],
        messages=[{"role": "user", "content": prompt}],
        temperature=config["agents"]["resource"]["temperature"],
        max_tokens=config["agents"]["resource"]["max_tokens"],
    )

    result = json.loads(response.choices[0].message.content)
    return result
```

### agents/response.py

```python
import mlflow
from domino.agents.tracing import add_tracing
from openai import OpenAI
import yaml
import json

mlflow.openai.autolog()
client = OpenAI()

with open("config.yaml") as f:
    config = yaml.safe_load(f)

def response_evaluator(inputs, output):
    """Evaluate response draft quality."""
    message = output.get("message", "")
    return {
        "response_length": len(message),
        "has_all_audiences": 1.0 if len(output.get("audiences", [])) >= 2 else 0.0,
        "has_action_items": 1.0 if output.get("action_items") else 0.0,
    }

@add_tracing(name="response_agent", evaluator=response_evaluator)
def draft_response(
    incident: dict,
    classification: dict,
    impact: dict,
    resources: dict
) -> dict:
    """
    Generate communications for stakeholders.

    Args:
        incident: Original incident data
        classification: Output from classifier agent
        impact: Output from impact agent
        resources: Output from resource agent

    Returns:
        Dict with 'message', 'audiences', 'action_items', 'follow_up_time'
    """
    prompt = f"""
    Draft an incident response communication:

    Incident: {incident.get('title', 'N/A')}
    Category: {classification['category']}
    Urgency: {classification['urgency']}
    Impact Score: {impact['score']}
    Affected Users: {impact.get('affected_users', 'Unknown')}
    ETA: {resources.get('eta', 'Unknown')}

    Create:
    1. A clear, professional message
    2. Identify all audiences who need to be notified
    3. List action items
    4. Suggest follow-up time

    Respond in JSON format:
    {{
        "message": "<the communication message>",
        "audiences": ["<audience1>", "<audience2>"],
        "action_items": ["<action1>", "<action2>"],
        "follow_up_time": "<time>"
    }}
    """

    response = client.chat.completions.create(
        model=config["models"]["primary"],
        messages=[{"role": "user", "content": prompt}],
        temperature=config["agents"]["response"]["temperature"],
        max_tokens=config["agents"]["response"]["max_tokens"],
    )

    result = json.loads(response.choices[0].message.content)
    return result
```

## Pipeline with Tracing

### evaluators/pipeline_evaluator.py

```python
def pipeline_evaluator(inputs, output):
    """
    Evaluate the full pipeline output.

    This evaluator runs after all agents complete and scores
    the final result.
    """
    scores = {}

    # Classification quality
    classification = output.get("classification", {})
    scores["classification_confidence"] = classification.get("confidence", 0)

    # Impact assessment
    impact = output.get("impact", {})
    scores["impact_score"] = impact.get("score", 0) / 10.0  # Normalize to 0-1

    # Resource matching
    resources = output.get("resources", {})
    scores["resource_coverage"] = min(len(resources.get("responders", [])) / 3, 1.0)
    scores["meets_sla"] = 1.0 if resources.get("meets_sla", False) else 0.0

    # Response quality
    response = output.get("response", {})
    scores["response_completeness"] = (
        (1.0 if response.get("message") else 0.0) * 0.4 +
        (min(len(response.get("audiences", [])) / 2, 1.0)) * 0.3 +
        (min(len(response.get("action_items", [])) / 3, 1.0)) * 0.3
    )

    # Overall quality
    scores["overall_quality"] = (
        scores["classification_confidence"] * 0.25 +
        scores["impact_score"] * 0.25 +
        scores["resource_coverage"] * 0.25 +
        scores["response_completeness"] * 0.25
    )

    return scores
```

### main.py

```python
import mlflow
from domino.agents.tracing import add_tracing
from domino.agents.logging import DominoRun

from agents.classifier import classify_incident
from agents.impact import assess_impact
from agents.resource import match_resources
from agents.response import draft_response
from evaluators.pipeline_evaluator import pipeline_evaluator

# Enable auto-tracing
mlflow.openai.autolog()

@add_tracing(name="triage_pipeline", evaluator=pipeline_evaluator)
def triage_incident(incident: dict) -> dict:
    """
    Full incident triage pipeline.

    Orchestrates all agents and returns complete triage result.
    """
    # Step 1: Classify
    classification = classify_incident(incident)

    # Step 2: Assess Impact
    impact = assess_impact(incident, classification)

    # Step 3: Match Resources
    resources = match_resources(incident, classification, impact)

    # Step 4: Draft Response
    response = draft_response(incident, classification, impact, resources)

    return {
        "incident_id": incident.get("id"),
        "classification": classification,
        "impact": impact,
        "resources": resources,
        "response": response,
    }


def main():
    # Define aggregated metrics for the run
    aggregated_metrics = [
        ("classification_confidence", "mean"),
        ("classification_confidence", "min"),
        ("impact_score", "median"),
        ("meets_sla", "mean"),
        ("overall_quality", "mean"),
        ("overall_quality", "stdev"),
    ]

    # Sample incidents for testing
    test_incidents = [
        {
            "id": "INC-001",
            "title": "Database connection failures",
            "description": "Multiple users reporting inability to access the main application. Database logs show connection pool exhaustion.",
            "source": "monitoring-alert",
        },
        {
            "id": "INC-002",
            "title": "Suspicious login attempts detected",
            "description": "Security system flagged unusual login patterns from multiple IPs targeting admin accounts.",
            "source": "security-siem",
        },
        {
            "id": "INC-003",
            "title": "API response times degraded",
            "description": "Customer-facing API endpoints showing 5x normal latency. No errors, just slow responses.",
            "source": "apm-alert",
        },
    ]

    # Run with full tracing
    with DominoRun(
        run_name="incident-triage-evaluation",
        agent_config_path="config.yaml",
        custom_summary_metrics=aggregated_metrics
    ) as run:
        results = []

        for incident in test_incidents:
            print(f"\nProcessing: {incident['id']} - {incident['title']}")

            result = triage_incident(incident)
            results.append(result)

            # Print summary
            print(f"  Category: {result['classification']['category']}")
            print(f"  Urgency: {result['classification']['urgency']}")
            print(f"  Impact: {result['impact']['score']}/10")
            print(f"  SLA Met: {result['resources']['meets_sla']}")

        print(f"\n{'='*50}")
        print(f"Run completed: {run.run_id}")
        print(f"Processed {len(results)} incidents")

    return results


if __name__ == "__main__":
    main()
```

## Viewing Results in Domino

### Navigate to Traces

1. Go to your Domino project
2. Click **Experiments** in the sidebar
3. Find experiment: `tracing-{your-username}`
4. Click on the run: `incident-triage-evaluation`
5. View the **Traces** tab

### Trace Hierarchy

```
triage_pipeline (INC-001)
├── classifier_agent
│   └── [OpenAI gpt-4o-mini call]
├── impact_agent
│   └── [OpenAI gpt-4o-mini call]
├── resource_agent
│   └── [OpenAI gpt-4o-mini call]
└── response_agent
    └── [OpenAI gpt-4o-mini call]
```

### Aggregated Metrics

The run's metrics page shows:
- `classification_confidence_mean`
- `classification_confidence_min`
- `impact_score_median`
- `meets_sla_mean`
- `overall_quality_mean`
- `overall_quality_stdev`

## requirements.txt

```text
mlflow==3.2.0
dominodatalab[data,aisystems] @ git+https://github.com/dominodatalab/python-domino.git@master
openai>=1.0.0
pyyaml>=6.0
```

## Blueprint Reference

Full implementation available at:
https://github.com/dominodatalab/GenAI-Tracing-Tutorial
