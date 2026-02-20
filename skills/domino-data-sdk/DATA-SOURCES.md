# Domino Data Sources

The `DataSourceClient` provides access to configured data sources in Domino, including SQL databases and object stores.

## DataSourceClient

### Initialization

```python
from domino_data.data_sources import DataSourceClient

# Auto-configured inside Domino
client = DataSourceClient()
```

### Get Data Source

```python
# Fetch by name (as configured in Domino)
ds = client.get_datasource("my-data-source")

# Properties
print(ds.name)           # Data source name
print(ds.datasource_type) # Type (e.g., 'redshift', 's3')
print(ds.auth_type)      # Authentication type
print(ds.owner)          # Owner username
```

## Tabular Data Sources (SQL)

For SQL-queryable sources like Redshift, Snowflake, PostgreSQL:

### Execute Queries

```python
# Get tabular data source
ds = client.get_datasource("analytics-db")

# Execute SQL query
result = ds.query("""
    SELECT customer_id, revenue, region
    FROM sales
    WHERE date >= '2024-01-01'
    LIMIT 10000
""")

# Convert to pandas DataFrame
df = result.to_pandas()
print(df.head())

# Save directly to parquet
result.to_parquet("sales_data.parquet")
```

### Configuration Override

```python
from domino_data.data_sources import DatasourceConfig

# Override configuration for this session
config = DatasourceConfig(
    schema="production",
    warehouse="COMPUTE_WH"
)
ds.update(config)

# Query with new config
result = ds.query("SELECT * FROM users")

# Reset to default
ds.reset_config()
```

## Object Store Data Sources (S3, GCS, Azure Blob)

For object storage sources:

### List Objects

```python
ds = client.get_datasource("data-lake")

# List all objects
objects = ds.list_objects()

# List with prefix filter
objects = ds.list_objects(prefix="raw/2024/", page_size=500)

for obj in objects:
    print(obj.key)
```

### Download Files

```python
# Download single file
ds.download_file("data/input.csv", "local_input.csv")

# Get object and download with parallelism
obj = ds.Object("large-file.parquet")
obj.download("local_file.parquet", max_workers=8)

# Get content as bytes
content = ds.get("config.json")
data = json.loads(content)
```

### Upload Files

```python
# Upload bytes
ds.put("output/results.json", json.dumps(data).encode())

# Upload file
obj = ds.Object("output/model.pkl")
obj.upload_file("trained_model.pkl")
```

### Signed URLs

```python
# Get read-only signed URL
read_url = ds.get_key_url("data/file.csv", is_read_write=False)

# Get read-write signed URL
write_url = ds.get_key_url("output/file.csv", is_read_write=True)
```

## Object Operations

The `_Object` class represents individual objects:

```python
obj = ds.Object("path/to/file.csv")

# Get content
content = obj.get()

# Download to file
obj.download_file("local.csv")

# Download with parallelism (for large files)
obj.download("local.csv", max_workers=4)

# Upload content
obj.put(b"new content here")

# Upload from file
obj.upload_file("source.csv")

# Get HTTP client for custom operations
http_client = obj.http()
```

## Supported Data Source Types

| Type | Class | Operations |
|------|-------|------------|
| Redshift | TabularDatasource | SQL queries |
| Snowflake | TabularDatasource | SQL queries |
| PostgreSQL | TabularDatasource | SQL queries |
| MySQL | TabularDatasource | SQL queries |
| S3 | ObjectStoreDatasource | Object CRUD |
| GCS | ObjectStoreDatasource | Object CRUD |
| Azure Blob | ObjectStoreDatasource | Object CRUD |
| ADLS Gen2 | ObjectStoreDatasource | Object CRUD |

## Error Handling

```python
from domino_data.data_sources import (
    DominoError,
    UnauthenticatedError
)

try:
    result = ds.query("SELECT * FROM table")
    df = result.to_pandas()
except UnauthenticatedError:
    # Handle auth failure with exponential backoff
    print("Authentication failed")
except DominoError as e:
    print(f"Query failed: {e}")
```

## Performance Tips

1. **Use pagination**: Set `page_size` when listing many objects
2. **Parallel downloads**: Use `max_workers` for large files
3. **Stream results**: Use `to_parquet()` for large query results
4. **Reuse clients**: Keep `DataSourceClient` instance for multiple queries
5. **Config override**: Use `update()` for session-specific settings
