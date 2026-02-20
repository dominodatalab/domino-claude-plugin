# Domino Training Sets

Training Sets provide versioned, reproducible datasets for machine learning. The `training_sets` module enables programmatic management of training data.

## Overview

Training Sets help you:
- Version your training data for reproducibility
- Track schema and metadata across versions
- Query and filter training set versions
- Integrate with ML pipelines

## Installation

```python
from domino_data.training_sets import (
    create_training_set_version,
    get_training_set,
    get_training_set_version,
    list_training_sets,
    list_training_set_versions,
    update_training_set,
    update_training_set_version,
    delete_training_set,
    delete_training_set_version
)
```

## Create Training Set Version

```python
import pandas as pd
from domino_data.training_sets import create_training_set_version

# Prepare your training data
df = pd.DataFrame({
    "customer_id": [1, 2, 3, 4, 5],
    "feature_a": [0.1, 0.2, 0.3, 0.4, 0.5],
    "feature_b": [10, 20, 30, 40, 50],
    "label": [1, 0, 1, 0, 1]
})

# Create a new version
version = create_training_set_version(
    training_set_name="customer-churn-model",
    df=df,
    key_columns=["customer_id"],
    description="Initial training data - Q1 2024"
)

print(f"Created version: {version.number}")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `training_set_name` | str | Name of the training set |
| `df` | DataFrame | Training data |
| `key_columns` | List[str] | Columns that uniquely identify rows |
| `description` | str | Version description |

## Get Training Set

```python
from domino_data.training_sets import get_training_set

# Retrieve training set metadata
ts = get_training_set("customer-churn-model")

print(f"Name: {ts.name}")
print(f"Created: {ts.created_at}")
print(f"Versions: {ts.version_count}")
```

## Get Specific Version

```python
from domino_data.training_sets import get_training_set_version

# Get version by number
version = get_training_set_version(
    training_set_name="customer-churn-model",
    number=1
)

print(f"Version: {version.number}")
print(f"Description: {version.description}")
print(f"Row count: {version.row_count}")
```

## List Training Sets

```python
from domino_data.training_sets import list_training_sets

# List all training sets
all_sets = list_training_sets()

for ts in all_sets:
    print(f"{ts.name}: {ts.version_count} versions")

# Filter with metadata
filtered = list_training_sets(
    meta={"project": "churn-prediction"},
    asc=False,
    offset=0,
    limit=10
)
```

## List Versions

```python
from domino_data.training_sets import list_training_set_versions

# List all versions of a training set
versions = list_training_set_versions(
    training_set_name="customer-churn-model"
)

for v in versions:
    print(f"v{v.number}: {v.description}")

# Filter versions
recent = list_training_set_versions(
    training_set_name="customer-churn-model",
    meta={"status": "production"},
    asc=False,
    limit=5
)
```

## Update Training Set

```python
from domino_data.training_sets import update_training_set

# Update metadata
ts = get_training_set("customer-churn-model")
ts.description = "Updated description"
ts.meta = {"project": "churn-v2", "team": "ml-ops"}

update_training_set(ts)
```

## Update Version

```python
from domino_data.training_sets import update_training_set_version

# Update version metadata
version = get_training_set_version("customer-churn-model", 1)
version.description = "Production training data"
version.meta = {"status": "production"}

update_training_set_version(version)
```

## Delete Training Set

```python
from domino_data.training_sets import delete_training_set

# Only works if no versions exist
delete_training_set("old-training-set")
```

## Delete Version

```python
from domino_data.training_sets import delete_training_set_version

# Delete specific version
delete_training_set_version(
    training_set_name="customer-churn-model",
    number=1
)
```

## Error Handling

```python
from domino_data.training_sets import (
    ServerException,
    SchemaMismatchException
)

try:
    version = create_training_set_version(
        training_set_name="my-data",
        df=df,
        key_columns=["id"]
    )
except SchemaMismatchException:
    print("DataFrame columns don't match existing schema")
except ServerException as e:
    print(f"Server rejected request: {e}")
```

## Best Practices

1. **Meaningful names**: Use descriptive training set names
2. **Key columns**: Always specify columns that uniquely identify rows
3. **Versioning**: Create new versions for each training run
4. **Metadata**: Use `meta` field for filtering and organization
5. **Descriptions**: Document what changed in each version
6. **Schema consistency**: Maintain consistent columns across versions

## Common Patterns

### Training Pipeline Integration

```python
from domino_data.training_sets import (
    create_training_set_version,
    get_training_set_version
)
import mlflow

# Create training version
version = create_training_set_version(
    training_set_name="model-training-data",
    df=training_df,
    key_columns=["id"],
    description=f"Training run {mlflow.active_run().info.run_id}"
)

# Log to MLflow
mlflow.log_param("training_set_version", version.number)
```

### Data Validation

```python
# Validate before creating version
def validate_training_data(df):
    assert not df.isnull().any().any(), "No nulls allowed"
    assert len(df) > 100, "Need at least 100 samples"
    return True

if validate_training_data(df):
    create_training_set_version(
        training_set_name="validated-data",
        df=df,
        key_columns=["id"]
    )
```
