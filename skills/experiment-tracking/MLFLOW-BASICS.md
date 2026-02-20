# MLflow Basics for Domino Experiment Tracking

This guide covers the fundamentals of using MLflow for experiment tracking in Domino Data Lab.

## Setting Up an Experiment

### Unique Experiment Names

**CRITICAL**: Experiment names must be unique across the entire Domino deployment, not just your project.

```python
import mlflow
import os

def setup_experiment(base_name: str = "experiment"):
    """
    Set up a Domino-compatible MLflow experiment.

    Automatically appends username to ensure uniqueness.
    """
    username = os.environ.get('DOMINO_STARTING_USERNAME', 'unknown')
    project = os.environ.get('DOMINO_PROJECT_NAME', 'unknown')

    # Unique name format
    experiment_name = f"{base_name}-{project}-{username}"

    mlflow.set_experiment(experiment_name)
    print(f"Experiment set: {experiment_name}")

    return experiment_name
```

### Adding Domino Context as Tags

```python
def log_domino_context():
    """Log Domino environment information as tags."""
    mlflow.set_tags({
        "domino.user": os.environ.get('DOMINO_STARTING_USERNAME', 'unknown'),
        "domino.project": os.environ.get('DOMINO_PROJECT_NAME', 'unknown'),
        "domino.run_id": os.environ.get('DOMINO_RUN_ID', 'unknown'),
        "domino.hardware_tier": os.environ.get('DOMINO_HARDWARE_TIER_NAME', 'unknown'),
    })
```

## Auto-Logging

Auto-logging is the easiest way to track experiments. MLflow automatically captures parameters, metrics, and models.

### Framework-Specific Auto-Logging

```python
# Scikit-learn
mlflow.sklearn.autolog()

# TensorFlow/Keras
mlflow.tensorflow.autolog()

# PyTorch
mlflow.pytorch.autolog()

# XGBoost
mlflow.xgboost.autolog()

# LightGBM
mlflow.lightgbm.autolog()

# CatBoost
mlflow.catboost.autolog()

# Spark
mlflow.spark.autolog()

# FastAI
mlflow.fastai.autolog()
```

### Enable All Auto-Logging

```python
# Enable auto-logging for all supported frameworks
mlflow.autolog()
```

### Auto-Logging Options

```python
mlflow.sklearn.autolog(
    log_input_examples=True,      # Log sample inputs
    log_model_signatures=True,    # Log model input/output schema
    log_models=True,              # Log trained models
    log_datasets=True,            # Log dataset info
    disable=False,                # Enable/disable
    exclusive=False,              # Only log from this framework
    disable_for_unsupported_versions=False,
    silent=False,                 # Suppress warnings
    max_tuning_runs=5,            # Max hyperparameter tuning runs
    log_post_training_metrics=True,
)
```

### Complete Auto-Logging Example

```python
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris

# Setup
mlflow.set_experiment("iris-classification-jsmith")
mlflow.sklearn.autolog()

# Load data
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2
)

# Train - MLflow automatically logs everything
with mlflow.start_run(run_name="random-forest-v1"):
    model = RandomForestClassifier(n_estimators=100, max_depth=5)
    model.fit(X_train, y_train)

    # Auto-logged: parameters, metrics, model artifact
    # Manual addition for custom metrics
    test_accuracy = model.score(X_test, y_test)
    mlflow.log_metric("test_accuracy", test_accuracy)
```

## Manual Logging

For finer control, log items manually.

### Parameters

```python
with mlflow.start_run(run_name="manual-logging-example"):
    # Single parameter
    mlflow.log_param("learning_rate", 0.01)

    # Multiple parameters
    mlflow.log_params({
        "epochs": 100,
        "batch_size": 32,
        "optimizer": "adam",
        "hidden_layers": [64, 32],
    })
```

### Metrics

```python
with mlflow.start_run():
    # Single metric
    mlflow.log_metric("accuracy", 0.95)

    # Metric at specific step (for training curves)
    for epoch in range(100):
        train_loss = train_epoch()
        val_loss = validate()

        mlflow.log_metric("train_loss", train_loss, step=epoch)
        mlflow.log_metric("val_loss", val_loss, step=epoch)

    # Multiple metrics
    mlflow.log_metrics({
        "precision": 0.94,
        "recall": 0.92,
        "f1": 0.93,
    })
```

### Artifacts

```python
with mlflow.start_run():
    # Single file
    mlflow.log_artifact("confusion_matrix.png")

    # Entire directory
    mlflow.log_artifacts("output_folder/")

    # With subdirectory in artifact store
    mlflow.log_artifact("report.pdf", artifact_path="reports")

    # Log text directly
    mlflow.log_text("Model performed well on test set", "notes.txt")

    # Log dictionary as JSON
    mlflow.log_dict({"config": "value"}, "config.json")

    # Log figure
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    mlflow.log_figure(fig, "plot.png")
```

### Models

```python
with mlflow.start_run():
    # Scikit-learn model
    mlflow.sklearn.log_model(model, "sklearn_model")

    # PyTorch model
    mlflow.pytorch.log_model(model, "pytorch_model")

    # TensorFlow/Keras model
    mlflow.tensorflow.log_model(model, "tf_model")

    # Generic Python model
    mlflow.pyfunc.log_model(
        artifact_path="custom_model",
        python_model=MyCustomModel(),
        conda_env="conda.yaml"
    )
```

## Large Artifact Upload

For large files (LLMs, deep learning models), enable multipart upload:

```python
import os

# Enable multipart upload for large files
os.environ['MLFLOW_ENABLE_PROXY_MULTIPART_UPLOAD'] = "true"
os.environ['MLFLOW_MULTIPART_UPLOAD_CHUNK_SIZE'] = "104857600"  # 100MB chunks

with mlflow.start_run():
    mlflow.log_artifact("large_model.bin")
```

## Tags

Use tags for metadata that isn't a parameter:

```python
with mlflow.start_run():
    # Single tag
    mlflow.set_tag("model_type", "classification")

    # Multiple tags
    mlflow.set_tags({
        "team": "ml-platform",
        "priority": "high",
        "dataset_version": "v2.1",
    })
```

## Run Names and Descriptions

```python
# Set run name
with mlflow.start_run(run_name="experiment-baseline-v1"):
    pass

# Set description
with mlflow.start_run(run_name="final-model", description="Production candidate"):
    pass

# Update description after run
mlflow.set_tag("mlflow.note.content", "This run achieved best results")
```

## Nested Runs

For hyperparameter tuning or cross-validation:

```python
with mlflow.start_run(run_name="hyperparameter-search"):
    # Parent run
    mlflow.log_param("search_space", "grid")

    for lr in [0.01, 0.001, 0.0001]:
        with mlflow.start_run(run_name=f"lr-{lr}", nested=True):
            # Child run
            mlflow.log_param("learning_rate", lr)
            accuracy = train_and_evaluate(lr)
            mlflow.log_metric("accuracy", accuracy)
```

## Complete Example

```python
import mlflow
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.datasets import load_wine
from sklearn.metrics import classification_report
import json

# Setup experiment with unique name
username = os.environ.get('DOMINO_STARTING_USERNAME', 'dev')
mlflow.set_experiment(f"wine-classification-{username}")

# Load data
wine = load_wine()
X_train, X_test, y_train, y_test = train_test_split(
    wine.data, wine.target, test_size=0.2, random_state=42
)

# Training run
with mlflow.start_run(run_name="random-forest-optimized"):
    # Log Domino context
    mlflow.set_tags({
        "domino.user": username,
        "domino.project": os.environ.get('DOMINO_PROJECT_NAME', 'dev'),
        "model_type": "random_forest",
    })

    # Hyperparameters
    params = {
        "n_estimators": 200,
        "max_depth": 10,
        "min_samples_split": 5,
        "random_state": 42,
    }
    mlflow.log_params(params)

    # Train model
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    # Metrics
    train_accuracy = model.score(X_train, y_train)
    test_accuracy = model.score(X_test, y_test)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)

    mlflow.log_metrics({
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "cv_mean": cv_scores.mean(),
        "cv_std": cv_scores.std(),
    })

    # Classification report as artifact
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    mlflow.log_dict(report, "classification_report.json")

    # Feature importance
    importance = dict(zip(wine.feature_names, model.feature_importances_))
    mlflow.log_dict(importance, "feature_importance.json")

    # Log model
    mlflow.sklearn.log_model(
        model,
        "model",
        input_example=X_test[:5],
    )

    print(f"Run ID: {mlflow.active_run().info.run_id}")
    print(f"Test Accuracy: {test_accuracy:.4f}")
```
