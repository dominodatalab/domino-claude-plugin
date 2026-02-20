---
name: domino-experiment-tracking
description: Track traditional ML experiments in Domino using the MLflow-based Experiment Manager. Covers experiment setup, auto-logging for sklearn/TensorFlow/PyTorch, manual logging, artifact storage, run comparison, and model registration. Use when training ML models, logging metrics and parameters, comparing model runs, or registering models.
---

# Domino Experiment Tracking Skill

This skill provides comprehensive knowledge for tracking ML experiments in Domino Data Lab using the built-in MLflow-based Experiment Manager.

## Key Concepts

### Experiment Manager Overview

Domino's Experiment Manager is built on MLflow and provides:
- Automatic and manual logging of parameters, metrics, and artifacts
- Run comparison and visualization
- Model versioning and registry
- Integration with Domino projects and jobs

### Critical Configuration

**Experiment names must be unique across the entire Domino deployment.** Always append username or project name to ensure uniqueness.

## Related Documentation

- [MLFLOW-BASICS.md](./MLFLOW-BASICS.md) - Auto-logging, manual logging
- [COMPARING-RUNS.md](./COMPARING-RUNS.md) - Run comparison, export
- [MODEL-REGISTRY.md](./MODEL-REGISTRY.md) - Model registration & stages

## Quick Start

```python
import mlflow
import os

# CRITICAL: Experiment names must be unique across Domino deployment
username = os.environ.get('DOMINO_STARTING_USERNAME', 'unknown')
experiment_name = f"my-experiment-{username}"

# Set the experiment
mlflow.set_experiment(experiment_name)

# Enable auto-logging (easiest approach)
mlflow.autolog()

# Run training
with mlflow.start_run(run_name="my-first-run"):
    model.fit(X_train, y_train)

    # Optional: manually log additional items
    mlflow.log_param("custom_param", "value")
    mlflow.log_metric("custom_metric", 0.95)
```

## Supported Frameworks

| Framework | Auto-log Command |
|-----------|------------------|
| Scikit-learn | `mlflow.sklearn.autolog()` |
| TensorFlow/Keras | `mlflow.tensorflow.autolog()` |
| PyTorch | `mlflow.pytorch.autolog()` |
| XGBoost | `mlflow.xgboost.autolog()` |
| LightGBM | `mlflow.lightgbm.autolog()` |
| All at once | `mlflow.autolog()` |

## Environment Variables

Domino automatically configures MLflow to use the built-in tracking server. These variables are pre-set:

| Variable | Description |
|----------|-------------|
| `MLFLOW_TRACKING_URI` | Domino's MLflow server URL |
| `DOMINO_STARTING_USERNAME` | User running the experiment |
| `DOMINO_PROJECT_NAME` | Current project name |
| `DOMINO_RUN_ID` | Domino job run ID |

## Documentation Links

- Domino Experiment Tracking: https://docs.dominodatalab.com/en/latest/user_guide/da707d/track-and-monitor-experiments/
- Domino Model Registry: https://docs.dominodatalab.com/en/latest/user_guide/3b6ae5/manage-models-with-model-registry/
