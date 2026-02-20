# Domino Model Registry

This guide covers registering, versioning, and managing models in Domino's Model Registry.

## Overview

The Model Registry provides:
- Centralized model storage
- Version tracking
- Stage transitions (Staging → Production)
- Model lineage and metadata
- Access control

## Registering Models

### Register During Training

```python
import mlflow

with mlflow.start_run():
    # Train model
    model.fit(X_train, y_train)

    # Log and register in one step
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name="wine-classifier"
    )
```

### Register Existing Run

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Register model from existing run
result = client.create_model_version(
    name="wine-classifier",
    source=f"runs:/{run_id}/model",
    run_id=run_id
)

print(f"Registered version: {result.version}")
```

### Register with URI

```python
import mlflow

# Register from artifact URI
mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="wine-classifier"
)
```

## Model Versions

### List Versions

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get all versions of a model
versions = client.search_model_versions("name='wine-classifier'")

for v in versions:
    print(f"Version {v.version}: {v.current_stage} - Run: {v.run_id}")
```

### Get Specific Version

```python
# Get version details
version = client.get_model_version(
    name="wine-classifier",
    version="3"
)

print(f"Source: {version.source}")
print(f"Stage: {version.current_stage}")
print(f"Description: {version.description}")
```

### Update Version Description

```python
client.update_model_version(
    name="wine-classifier",
    version="3",
    description="Improved accuracy with feature engineering"
)
```

## Stage Transitions

### Model Stages

| Stage | Purpose |
|-------|---------|
| `None` | Initial state, not assigned |
| `Staging` | Ready for testing/validation |
| `Production` | Approved for production use |
| `Archived` | Deprecated, kept for reference |

### Transition Model Stage

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Move to staging
client.transition_model_version_stage(
    name="wine-classifier",
    version="3",
    stage="Staging"
)

# Promote to production
client.transition_model_version_stage(
    name="wine-classifier",
    version="3",
    stage="Production"
)

# Archive old version
client.transition_model_version_stage(
    name="wine-classifier",
    version="2",
    stage="Archived"
)
```

### Archive Previous Production

```python
# When promoting new version, archive previous production
client.transition_model_version_stage(
    name="wine-classifier",
    version="3",
    stage="Production",
    archive_existing_versions=True  # Archives current Production version
)
```

## Loading Registered Models

### Load by Name and Version

```python
import mlflow

# Load specific version
model = mlflow.sklearn.load_model(
    model_uri="models:/wine-classifier/3"
)

predictions = model.predict(X_test)
```

### Load by Stage

```python
# Load production model
production_model = mlflow.sklearn.load_model(
    model_uri="models:/wine-classifier/Production"
)

# Load staging model
staging_model = mlflow.sklearn.load_model(
    model_uri="models:/wine-classifier/Staging"
)

# Load latest version
latest_model = mlflow.sklearn.load_model(
    model_uri="models:/wine-classifier/latest"
)
```

## Model Metadata

### Add Tags to Model

```python
client = MlflowClient()

# Model-level tags
client.set_registered_model_tag(
    name="wine-classifier",
    key="team",
    value="ml-platform"
)

# Version-level tags
client.set_model_version_tag(
    name="wine-classifier",
    version="3",
    key="validated",
    value="true"
)
```

### Add Aliases

```python
# Create alias for easy reference
client.set_registered_model_alias(
    name="wine-classifier",
    alias="champion",
    version="3"
)

# Load by alias
model = mlflow.sklearn.load_model("models:/wine-classifier@champion")
```

### Get Model Details

```python
# Get registered model info
model_info = client.get_registered_model("wine-classifier")

print(f"Name: {model_info.name}")
print(f"Description: {model_info.description}")
print(f"Tags: {model_info.tags}")
print(f"Latest versions: {model_info.latest_versions}")
```

## Model Lineage

### View Run Associated with Version

```python
version = client.get_model_version(
    name="wine-classifier",
    version="3"
)

# Get the source run
run = mlflow.get_run(version.run_id)

print(f"Training run: {run.info.run_id}")
print(f"Parameters: {run.data.params}")
print(f"Metrics: {run.data.metrics}")
```

### Track Data and Code Lineage

```python
with mlflow.start_run():
    # Log dataset info
    mlflow.set_tags({
        "dataset.name": "wine_data_v2",
        "dataset.version": "2024-01-15",
        "code.version": "git-abc123",
    })

    # Train and register
    model.fit(X_train, y_train)
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="wine-classifier"
    )
```

## Deleting Models

### Delete Model Version

```python
client = MlflowClient()

# Delete specific version
client.delete_model_version(
    name="wine-classifier",
    version="1"
)
```

### Delete Entire Model

```python
# Delete model and all versions
client.delete_registered_model(name="wine-classifier")
```

## Searching Models

### Search Registered Models

```python
from mlflow import MlflowClient

client = MlflowClient()

# Search by name pattern
models = client.search_registered_models(
    filter_string="name LIKE 'wine%'"
)

for model in models:
    print(f"{model.name}: {len(model.latest_versions)} versions")
```

### Search Model Versions

```python
# Find production models
production_versions = client.search_model_versions(
    filter_string="current_stage='Production'"
)

for v in production_versions:
    print(f"{v.name} v{v.version}")
```

## Model Signatures

### Log with Signature

```python
from mlflow.models.signature import infer_signature

with mlflow.start_run():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    # Infer signature from data
    signature = infer_signature(X_test, predictions)

    mlflow.sklearn.log_model(
        model,
        "model",
        signature=signature,
        input_example=X_test[:5],
        registered_model_name="wine-classifier"
    )
```

### View Signature

```python
import mlflow

model_info = mlflow.models.get_model_info("models:/wine-classifier/3")
print(f"Signature: {model_info.signature}")
```

## Complete Registry Workflow

```python
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.models.signature import infer_signature

# Setup
client = MlflowClient()
model_name = "wine-classifier"

# Training run
with mlflow.start_run(run_name="production-candidate"):
    # Train model
    model.fit(X_train, y_train)

    # Evaluate
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)

    mlflow.log_metrics({
        "train_accuracy": train_acc,
        "test_accuracy": test_acc
    })

    # Create signature
    signature = infer_signature(X_test, model.predict(X_test))

    # Register model
    mlflow.sklearn.log_model(
        model,
        "model",
        signature=signature,
        input_example=X_test[:3],
        registered_model_name=model_name
    )

    run_id = mlflow.active_run().info.run_id

# Get newly created version
versions = client.search_model_versions(f"name='{model_name}' and run_id='{run_id}'")
new_version = versions[0].version

print(f"Created model version: {new_version}")

# Move to staging for validation
client.transition_model_version_stage(
    name=model_name,
    version=new_version,
    stage="Staging"
)

# After validation, promote to production
client.transition_model_version_stage(
    name=model_name,
    version=new_version,
    stage="Production",
    archive_existing_versions=True
)

# Set champion alias
client.set_registered_model_alias(
    name=model_name,
    alias="champion",
    version=new_version
)

print(f"Model {model_name} v{new_version} is now in Production")

# Load and use
production_model = mlflow.sklearn.load_model(f"models:/{model_name}@champion")
predictions = production_model.predict(new_data)
```

## Documentation Links

- Domino Model Registry: https://docs.dominodatalab.com/en/latest/user_guide/3b6ae5/manage-models-with-model-registry/
- MLflow Model Registry: https://mlflow.org/docs/latest/model-registry.html
