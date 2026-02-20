---
name: domino-data-sdk
description: Use the domino-data Python SDK (dominodatalab-data) for programmatic data access in Domino. Covers DataSourceClient for SQL queries and object storage, DatasetClient for dataset files, TrainingSets for ML data versioning, Feature Store, and VectorDB (Pinecone) integration. Use when querying data sources, downloading datasets, managing training sets, or working with vector databases in Domino.
---

# Domino Data SDK Skill

This skill provides comprehensive knowledge for working with the `domino-data` Python SDK (`dominodatalab-data`) - the official library for Domino's Access Data features.

## Installation

```bash
# Via pip
pip install -U dominodatalab-data

# Via Poetry
poetry add dominodatalab-data

# In Domino environment (requirements.txt)
dominodatalab-data>=6.0.0
```

## Key Components

| Module | Purpose |
|--------|---------|
| `DataSourceClient` | Query SQL databases and access object stores |
| `DatasetClient` | Read files from Domino Datasets |
| `TrainingSets` | Version and manage ML training data |
| `Feature Store` | Manage ML features with Git integration |
| `VectorDB` | Pinecone vector database integration |

## Related Documentation

- [DATA-SOURCES.md](./DATA-SOURCES.md) - SQL queries and object storage
- [DATASETS.md](./DATASETS.md) - Dataset file operations
- [TRAINING-SETS.md](./TRAINING-SETS.md) - Training data versioning
- [VECTORDB.md](./VECTORDB.md) - Pinecone integration

## Quick Start

### Query a Data Source

```python
from domino_data.data_sources import DataSourceClient

# Initialize client (auto-configured in Domino)
client = DataSourceClient()

# Get a data source by name
ds = client.get_datasource("my-redshift-db")

# Execute SQL query
result = ds.query("SELECT * FROM customers WHERE region = 'US'")

# Convert to pandas DataFrame
df = result.to_pandas()

# Or save to parquet
result.to_parquet("output.parquet")
```

### Access Object Storage

```python
from domino_data.data_sources import DataSourceClient

client = DataSourceClient()
ds = client.get_datasource("my-s3-bucket")

# List objects
objects = ds.list_objects(prefix="data/", page_size=100)

# Download a file
ds.download_file("data/input.csv", "local_input.csv")

# Upload a file
ds.put("data/output.csv", open("results.csv", "rb").read())

# Get signed URL
url = ds.get_key_url("data/file.csv", is_read_write=False)
```

### Read from Datasets

```python
from domino_data.datasets import DatasetClient

client = DatasetClient()

# Get dataset by name
dataset = client.get_dataset("training-data")

# List files
files = dataset.list_files(prefix="images/")

# Download file
dataset.download("model.pkl", "local_model.pkl", max_workers=4)

# Get file content as bytes
content = dataset.get("config.json")
```

### Training Sets

```python
from domino_data.training_sets import (
    create_training_set_version,
    get_training_set,
    list_training_sets
)
import pandas as pd

# Create training set version from DataFrame
df = pd.DataFrame({
    "id": [1, 2, 3],
    "feature_a": [0.1, 0.2, 0.3],
    "label": [1, 0, 1]
})

version = create_training_set_version(
    training_set_name="customer-churn",
    df=df,
    key_columns=["id"],
    description="Initial training data"
)

# Get training set
ts = get_training_set("customer-churn")

# List all training sets
all_sets = list_training_sets()
```

### Vector Database (Pinecone)

```python
from domino_data.vectordb import (
    domino_pinecone3x_init_params,
    domino_pinecone3x_index_params
)
from pinecone import Pinecone

# Initialize Pinecone client with Domino credentials
init_params = domino_pinecone3x_init_params("my-pinecone-ds")
pc = Pinecone(**init_params)

# Get index parameters
index_params = domino_pinecone3x_index_params("my-pinecone-ds", "embeddings")
index = pc.Index(**index_params)

# Query vectors
results = index.query(
    vector=[0.1, 0.2, 0.3, ...],
    top_k=10,
    include_metadata=True
)
```

## Authentication

The library auto-configures authentication inside Domino workspaces and jobs:

```python
# Environment variables used automatically:
# DOMINO_USER_API_KEY - API key for authentication
# DOMINO_TOKEN_FILE - Token file location
# DOMINO_API_PROXY - API proxy URL
# DOMINO_DATA_API_GATEWAY - Data API gateway (default: http://127.0.0.1:8766)
```

For external use:

```python
import os
os.environ["DOMINO_USER_API_KEY"] = "your-api-key"
os.environ["DOMINO_API_HOST"] = "https://your-domino.com"

from domino_data.data_sources import DataSourceClient
client = DataSourceClient()
```

## Error Handling

```python
from domino_data.data_sources import DominoError, UnauthenticatedError

try:
    result = ds.query("SELECT * FROM table")
except UnauthenticatedError:
    print("Authentication failed - check API key")
except DominoError as e:
    print(f"Domino error: {e}")
```

## Best Practices

1. **Use within Domino**: Auth is automatic in workspaces/jobs
2. **Parallel downloads**: Use `max_workers` for large files
3. **Pagination**: Use `page_size` when listing many objects
4. **Training Sets**: Version your training data for reproducibility
5. **Connection reuse**: Reuse client instances when possible

## Package Info

- **PyPI**: `dominodatalab-data`
- **GitHub**: https://github.com/dominodatalab/domino-data
- **License**: Apache 2.0
- **Python**: 3.8+
