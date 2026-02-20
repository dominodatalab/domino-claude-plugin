# Comparing and Analyzing Experiment Runs

This guide covers how to compare experiment runs, search for specific runs, and export results in Domino Data Lab.

## Viewing Runs in Domino UI

### Accessing Experiment Manager

1. Navigate to your Domino project
2. Click **Experiments** in the left sidebar
3. Select your experiment by name
4. View the runs table with metrics, parameters, and status

### Run Comparison View

1. Select multiple runs using checkboxes
2. Click **Compare** button
3. View side-by-side comparison of:
   - Parameters
   - Metrics
   - Artifacts
   - Training curves

## Programmatic Run Search

### Search by Experiment

```python
import mlflow

# Get experiment by name
experiment = mlflow.get_experiment_by_name("my-experiment-jsmith")

# Search all runs in experiment
runs = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.accuracy DESC"]
)

print(runs[["run_id", "params.learning_rate", "metrics.accuracy"]])
```

### Filter Runs

```python
# Search with filter string (SQL-like syntax)
runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"],
    filter_string="metrics.accuracy > 0.9 AND params.model_type = 'random_forest'",
    order_by=["metrics.accuracy DESC"],
    max_results=10
)
```

### Filter String Syntax

| Operator | Example |
|----------|---------|
| `=` | `params.model = 'xgboost'` |
| `!=` | `params.model != 'baseline'` |
| `>`, `>=` | `metrics.accuracy > 0.9` |
| `<`, `<=` | `metrics.loss <= 0.1` |
| `LIKE` | `params.name LIKE '%test%'` |
| `AND` | `metrics.a > 0.8 AND metrics.b < 0.5` |
| `OR` | `params.model = 'a' OR params.model = 'b'` |

### Search by Tags

```python
runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"],
    filter_string="tags.team = 'ml-platform' AND tags.priority = 'high'"
)
```

### Search by Run Status

```python
# Only finished runs
runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"],
    filter_string="status = 'FINISHED'"
)

# Status values: RUNNING, SCHEDULED, FINISHED, FAILED, KILLED
```

## Getting Run Details

### Load Specific Run

```python
# Get run by ID
run = mlflow.get_run("abc123def456")

# Access run info
print(f"Run ID: {run.info.run_id}")
print(f"Status: {run.info.status}")
print(f"Start time: {run.info.start_time}")
print(f"End time: {run.info.end_time}")
print(f"Artifact URI: {run.info.artifact_uri}")

# Access parameters
print(f"Parameters: {run.data.params}")

# Access metrics
print(f"Metrics: {run.data.metrics}")

# Access tags
print(f"Tags: {run.data.tags}")
```

### Get Metric History

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get full history of a metric
history = client.get_metric_history(run_id="abc123", key="loss")

for metric in history:
    print(f"Step {metric.step}: {metric.value}")
```

## Downloading Artifacts

### Download All Artifacts

```python
# Download to local directory
local_path = mlflow.artifacts.download_artifacts(
    run_id="abc123def456",
    artifact_path="",  # Empty for all artifacts
    dst_path="./downloaded_artifacts"
)
```

### Download Specific Artifact

```python
# Download specific file
local_path = mlflow.artifacts.download_artifacts(
    run_id="abc123def456",
    artifact_path="model/model.pkl"
)
```

### List Artifacts

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
artifacts = client.list_artifacts(run_id="abc123def456")

for artifact in artifacts:
    print(f"{artifact.path} - {artifact.file_size} bytes")
```

## Loading Models from Runs

### Load Model by Run ID

```python
# Load sklearn model
model = mlflow.sklearn.load_model(f"runs:/abc123def456/model")

# Make predictions
predictions = model.predict(X_test)
```

### Load Model by URI

```python
# Load from artifact URI
model = mlflow.pyfunc.load_model(
    "mlflow-artifacts:/abc123def456/artifacts/model"
)
```

## Exporting Run Data

### Export to DataFrame

```python
import pandas as pd

# Get all runs as DataFrame
runs_df = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"]
)

# Export to CSV
runs_df.to_csv("experiment_runs.csv", index=False)
```

### Export to JSON

```python
import json

runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"],
    output_format="list"  # Returns list of dicts
)

with open("experiment_runs.json", "w") as f:
    json.dump(runs, f, indent=2, default=str)
```

## Comparing Runs Programmatically

### Best Run by Metric

```python
# Find best run
runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"],
    order_by=["metrics.accuracy DESC"],
    max_results=1
)

best_run_id = runs.iloc[0]["run_id"]
best_accuracy = runs.iloc[0]["metrics.accuracy"]
print(f"Best run: {best_run_id} with accuracy {best_accuracy}")
```

### Compare Parameters Across Runs

```python
runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"],
    filter_string="metrics.accuracy > 0.85"
)

# Analyze parameter impact
param_analysis = runs.groupby("params.learning_rate").agg({
    "metrics.accuracy": ["mean", "std", "count"]
})
print(param_analysis)
```

### Visualize Run Comparison

```python
import matplotlib.pyplot as plt

runs = mlflow.search_runs(
    experiment_names=["my-experiment-jsmith"]
)

# Scatter plot of two metrics
plt.figure(figsize=(10, 6))
plt.scatter(
    runs["params.learning_rate"].astype(float),
    runs["metrics.accuracy"],
    c=runs["params.n_estimators"].astype(float),
    cmap="viridis"
)
plt.xlabel("Learning Rate")
plt.ylabel("Accuracy")
plt.colorbar(label="N Estimators")
plt.title("Hyperparameter Analysis")
plt.savefig("hyperparameter_analysis.png")
```

## Managing Runs

### Delete Runs

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Delete a run (moves to trash)
client.delete_run(run_id="abc123def456")

# Restore a deleted run
client.restore_run(run_id="abc123def456")
```

### Update Run Tags

```python
client = MlflowClient()

# Add or update tag
client.set_tag(run_id="abc123def456", key="reviewed", value="true")

# Delete tag
client.delete_tag(run_id="abc123def456", key="reviewed")
```

### Rename Run

```python
client = MlflowClient()
client.set_tag(
    run_id="abc123def456",
    key="mlflow.runName",
    value="new-run-name"
)
```

## Complete Comparison Example

```python
import mlflow
import pandas as pd
import matplotlib.pyplot as plt

# Search for all completed runs
experiment_name = "model-optimization-jsmith"
runs = mlflow.search_runs(
    experiment_names=[experiment_name],
    filter_string="status = 'FINISHED'",
    order_by=["metrics.test_accuracy DESC"]
)

print(f"Found {len(runs)} completed runs")

# Display top 5 runs
print("\nTop 5 Runs:")
top_runs = runs.head()[["run_id", "params.model_type", "params.learning_rate",
                         "metrics.test_accuracy", "metrics.train_accuracy"]]
print(top_runs.to_string())

# Find best run
best_run = runs.iloc[0]
print(f"\nBest Run: {best_run['run_id']}")
print(f"  Model: {best_run['params.model_type']}")
print(f"  Test Accuracy: {best_run['metrics.test_accuracy']:.4f}")

# Load best model
best_model = mlflow.sklearn.load_model(f"runs:/{best_run['run_id']}/model")

# Parameter analysis
print("\nAccuracy by Model Type:")
model_analysis = runs.groupby("params.model_type")["metrics.test_accuracy"].agg(
    ["mean", "std", "count"]
)
print(model_analysis)

# Export results
runs.to_csv(f"{experiment_name}_results.csv", index=False)
print(f"\nResults exported to {experiment_name}_results.csv")
```
