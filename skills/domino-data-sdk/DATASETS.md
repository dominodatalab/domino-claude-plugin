# Domino Datasets API

The `DatasetClient` provides programmatic access to Domino Datasets for reading files.

## DatasetClient

### Initialization

```python
from domino_data.datasets import DatasetClient

# Auto-configured inside Domino
client = DatasetClient()
```

### Environment Variables

The client uses these environment variables (auto-set in Domino):

| Variable | Purpose |
|----------|---------|
| `DOMINO_USER_API_KEY` | API key for authentication |
| `DOMINO_TOKEN_FILE` | Token file location |
| `DOMINO_API_PROXY` | API proxy URL |

## Get Dataset

```python
# Fetch dataset by name
dataset = client.get_dataset("training-data")

# Dataset is now ready for file operations
```

## List Files

```python
# List all files
files = dataset.list_files()

# List with prefix filter
files = dataset.list_files(prefix="images/train/", page_size=500)

# Iterate through files
for f in files:
    print(f.name)
```

## Download Files

### Simple Download

```python
# Download file to local path
dataset.download_file("model.pkl", "local_model.pkl")
```

### Parallel Download (Large Files)

```python
# Download with multiple workers for speed
dataset.download(
    dataset_file_name="large_dataset.parquet",
    local_file_name="local_data.parquet",
    max_workers=8
)
```

### Download to File Object

```python
# Download to file-like object
with open("output.bin", "wb") as f:
    dataset.download_fileobj("binary_file.bin", f)

# Useful for streaming or in-memory processing
import io
buffer = io.BytesIO()
dataset.download_fileobj("data.json", buffer)
buffer.seek(0)
data = json.load(buffer)
```

## Get File Content

```python
# Get file content as bytes
content = dataset.get("config.json")

# Parse JSON
import json
config = json.loads(content)

# Read CSV
import pandas as pd
import io
csv_content = dataset.get("data.csv")
df = pd.read_csv(io.BytesIO(csv_content))
```

## Get Signed URLs

```python
# Get signed URL for direct access
url = dataset.get_file_url("large_file.zip")

# Use with requests or other HTTP clients
import requests
response = requests.get(url)
```

## File Object Operations

The `_File` class represents individual files:

```python
# Get file object
file = dataset.File("path/to/file.csv")

# Get content as bytes
content = file.get()

# Download to local file
file.download_file("local.csv")

# Download with parallelism
file.download("local.csv", max_workers=4)

# Download to file-like object
with open("output.csv", "wb") as f:
    file.download_fileobj(f)
```

## Configuration Override

```python
from domino_data.datasets import DatasetConfig

# Override configuration for this session
config = DatasetConfig(
    # Configuration options
)
dataset.update(config)

# Reset to default
dataset.reset_config()
```

## Error Handling

```python
from domino_data.datasets import DominoError, UnauthenticatedError

try:
    content = dataset.get("file.txt")
except UnauthenticatedError:
    print("Authentication failed - check credentials")
except DominoError as e:
    print(f"Dataset error: {e}")
except FileNotFoundError:
    print("File not found in dataset")
```

## Common Patterns

### Load Parquet Dataset

```python
import pandas as pd
import pyarrow.parquet as pq
import io

content = dataset.get("data.parquet")
df = pd.read_parquet(io.BytesIO(content))
```

### Load Multiple Files

```python
import pandas as pd

# List CSV files
files = dataset.list_files(prefix="data/", page_size=1000)
csv_files = [f for f in files if f.name.endswith('.csv')]

# Load and concatenate
dfs = []
for f in csv_files:
    content = dataset.get(f.name)
    dfs.append(pd.read_csv(io.BytesIO(content)))

combined_df = pd.concat(dfs, ignore_index=True)
```

### Stream Large Files

```python
# For very large files, use parallel download
dataset.download(
    "huge_file.parquet",
    "/tmp/huge_file.parquet",
    max_workers=16
)

# Then read with memory mapping
df = pd.read_parquet("/tmp/huge_file.parquet")
```

## Best Practices

1. **Use parallel downloads**: Set `max_workers` for large files
2. **Pagination**: Use `page_size` when listing many files
3. **Stream when possible**: Use `download_fileobj` for processing
4. **Cache locally**: Download frequently-used files once
5. **Handle errors**: Wrap operations in try/except
