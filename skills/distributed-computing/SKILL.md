---
name: domino-distributed-computing
description: Work with distributed computing frameworks in Domino including Apache Spark, Ray, and Dask clusters. Covers cluster configuration, on-demand clusters, choosing between frameworks, PySpark usage, and scaling workloads. Use when processing large datasets, parallel ML training, or running distributed compute jobs.
---

# Domino Distributed Computing Skill

## Description
This skill helps users work with distributed computing frameworks in Domino - Spark, Ray, and Dask clusters for scaling compute-intensive workloads.

## Activation
Activate this skill when users want to:
- Run Spark, Ray, or Dask clusters in Domino
- Scale data processing or ML training
- Configure distributed cluster settings
- Understand when to use each framework

## Supported Frameworks

| Framework | Best For |
|-----------|----------|
| **Apache Spark** | Large-scale data processing, SQL, ETL |
| **Ray** | Distributed ML, hyperparameter tuning, RL |
| **Dask** | Parallel pandas, NumPy at scale |
| **MPI** | Scientific computing, HPC workloads |

## When to Use Each Framework

### Spark
- Processing terabyte-scale data
- SQL analytics on big data
- ETL pipelines
- Structured data processing

### Ray
- Distributed model training
- Hyperparameter optimization
- Reinforcement learning
- Generic Python parallelization

### Dask
- Scaling pandas workflows
- Parallel NumPy operations
- Lazy evaluation needed
- Familiar pandas/NumPy API preferred

## Launching On-Demand Clusters

### Via Domino UI
1. Start a workspace or job
2. Check **Attach compute cluster**
3. Select:
   - **Cluster Type**: Spark, Ray, or Dask
   - **Worker Count**: Number of workers
   - **Hardware Tier**: Resources per worker
   - **Auto-scaling**: Enable/disable
4. Launch

### Via Python SDK
```python
from domino import Domino

domino = Domino("project-owner/project-name")

# Start workspace with Spark cluster
workspace = domino.workspace_start(
    hardware_tier_name="medium",
    cluster_config={
        "clusterType": "Spark",
        "workerCount": 4,
        "workerHardwareTier": "medium",
        "masterHardwareTier": "medium"
    }
)
```

## Apache Spark

### Connecting to Spark
```python
from pyspark.sql import SparkSession

# Domino auto-configures Spark
spark = SparkSession.builder.getOrCreate()

# Check configuration
print(f"Spark version: {spark.version}")
print(f"Executors: {spark.sparkContext.defaultParallelism}")
```

### Reading Data
```python
# Read CSV
df = spark.read.csv("/mnt/data/dataset/data.csv", header=True, inferSchema=True)

# Read Parquet
df = spark.read.parquet("/mnt/data/dataset/")

# Read from database
df = spark.read.jdbc(
    url="jdbc:postgresql://host:5432/db",
    table="schema.table",
    properties={"user": "user", "password": "pass"}
)
```

### Processing Data
```python
from pyspark.sql import functions as F

# Transformations
result = df.filter(F.col("value") > 100) \
    .groupBy("category") \
    .agg(F.mean("value").alias("avg_value")) \
    .orderBy("avg_value", ascending=False)

# Show results
result.show()
```

### Machine Learning with Spark MLlib
```python
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline

# Prepare features
assembler = VectorAssembler(
    inputCols=["feature1", "feature2", "feature3"],
    outputCol="features"
)

# Create model
rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="label",
    numTrees=100
)

# Build pipeline
pipeline = Pipeline(stages=[assembler, rf])
model = pipeline.fit(train_df)
predictions = model.transform(test_df)
```

### Writing Results
```python
# Write Parquet (recommended)
result.write.parquet("/mnt/artifacts/output/", mode="overwrite")

# Write CSV
result.write.csv("/mnt/artifacts/output.csv", header=True)
```

## Ray

### Connecting to Ray
```python
import ray

# Domino auto-initializes Ray
# Or manually connect
ray.init(address="auto")

print(f"Cluster resources: {ray.cluster_resources()}")
```

### Parallel Tasks
```python
import ray

@ray.remote
def process_item(item):
    # Your processing logic
    return item * 2

# Run in parallel
items = [1, 2, 3, 4, 5]
futures = [process_item.remote(item) for item in items]
results = ray.get(futures)
print(results)  # [2, 4, 6, 8, 10]
```

### Distributed Training with Ray Train
```python
from ray import train
from ray.train import ScalingConfig
from ray.train.torch import TorchTrainer

def train_func():
    # Training logic
    model = create_model()
    for epoch in range(10):
        train_epoch(model)
        train.report({"loss": loss})

trainer = TorchTrainer(
    train_func,
    scaling_config=ScalingConfig(num_workers=4, use_gpu=True)
)
result = trainer.fit()
```

### Hyperparameter Tuning with Ray Tune
```python
from ray import tune
from ray.tune import CLIReporter

def objective(config):
    # Training with hyperparameters
    model = train_model(
        learning_rate=config["lr"],
        batch_size=config["batch_size"]
    )
    return {"accuracy": accuracy}

analysis = tune.run(
    objective,
    config={
        "lr": tune.loguniform(1e-4, 1e-1),
        "batch_size": tune.choice([32, 64, 128])
    },
    num_samples=20,
    progress_reporter=CLIReporter()
)

print(f"Best config: {analysis.best_config}")
```

## Dask

### Connecting to Dask
```python
from dask.distributed import Client

# Domino auto-configures Dask
client = Client()

print(f"Dashboard: {client.dashboard_link}")
print(f"Workers: {len(client.scheduler_info()['workers'])}")
```

### Dask DataFrames (Parallel pandas)
```python
import dask.dataframe as dd

# Read large CSV files
df = dd.read_csv("/mnt/data/dataset/*.csv")

# Parallel operations (lazy)
result = df.groupby("category")["value"].mean()

# Execute
computed_result = result.compute()
```

### Dask Arrays (Parallel NumPy)
```python
import dask.array as da

# Create large array
x = da.random.random((100000, 100000), chunks=(1000, 1000))

# Operations (lazy)
result = x.mean()

# Compute
value = result.compute()
```

### Dask ML
```python
from dask_ml.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

# Distributed hyperparameter search
param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, 30]
}

grid_search = GridSearchCV(
    RandomForestClassifier(),
    param_grid,
    cv=3
)

grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")
```

## GPU Clusters

### Spark RAPIDS
```python
# Use GPU-accelerated Spark
spark = SparkSession.builder \
    .config("spark.rapids.sql.enabled", "true") \
    .getOrCreate()

# Operations automatically use GPU
df = spark.read.parquet("/mnt/data/large_dataset/")
result = df.groupBy("category").agg({"value": "mean"})
```

### Ray with GPUs
```python
@ray.remote(num_gpus=1)
def train_on_gpu():
    import torch
    device = torch.device("cuda")
    # GPU training logic
    return model

# Run on GPU workers
futures = [train_on_gpu.remote() for _ in range(4)]
```

## Autoscaling

### Enable Autoscaling
Configure clusters to scale based on workload:
```python
cluster_config = {
    "clusterType": "Spark",
    "workerCount": 2,
    "maxWorkerCount": 10,  # Scale up to 10
    "autoScaling": True
}
```

### Monitor Scaling
View cluster status in Domino UI or via dashboard URLs.

## Best Practices

### 1. Choose Right Framework
- SQL/ETL: Spark
- ML/Parallel Python: Ray
- Pandas at scale: Dask

### 2. Right-size Clusters
- Start small, scale up
- Monitor resource usage
- Use autoscaling when unsure

### 3. Data Locality
```python
# Keep data close to compute
# Use Domino Datasets or cloud storage in same region
df = spark.read.parquet("/mnt/data/dataset/")
```

### 4. Persist Intermediate Results
```python
# Cache frequently used DataFrames
df.cache()
df.persist()
```

## Troubleshooting

### Cluster Won't Start
- Check hardware tier availability
- Verify cluster environment builds
- Review cluster logs

### Out of Memory
- Increase worker memory
- Add more workers
- Optimize code (reduce shuffles)

### Slow Performance
- Check data locality
- Review partition sizes
- Monitor cluster dashboard

## Documentation Reference
- [On-demand distributed computing](https://docs.dominodatalab.com/en/latest/user_guide/8b4418/on-demand-distributed-computing/)
- [Spark, Dask, Ray comparison](https://domino.ai/blog/spark-dask-ray-choosing-the-right-framework)
- [Access data with Dask](https://docs.dominodatalab.com/en/latest/user_guide/0919a6/access-data-with-dask/)
