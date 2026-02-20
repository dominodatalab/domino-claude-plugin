# Domino Flows Basics

This guide covers the fundamentals of building workflows with Domino Flows.

## Task Definition

### Basic Task

```python
from flytekit import task

@task
def my_task(input_value: int) -> int:
    """
    A task is the basic unit of work.

    Requirements:
    - Must have type hints for all parameters and return value
    - Should be idempotent (same input = same output)
    - Runs as a separate Domino Job
    """
    result = input_value * 2
    return result
```

### Task with Multiple Outputs

```python
from flytekit import task
from typing import Tuple

@task
def process_data(data_path: str) -> Tuple[str, int, float]:
    """Return multiple values."""
    processed_path = process(data_path)
    num_records = count_records(processed_path)
    accuracy = calculate_accuracy(processed_path)

    return processed_path, num_records, accuracy
```

### Task with Named Outputs

```python
from flytekit import task
from typing import NamedTuple

class TrainingOutput(NamedTuple):
    model_path: str
    accuracy: float
    num_epochs: int

@task
def train_model(data_path: str, epochs: int) -> TrainingOutput:
    """Return named outputs for clarity."""
    model = train(data_path, epochs)
    accuracy = evaluate(model)

    return TrainingOutput(
        model_path="/mnt/artifacts/model.pkl",
        accuracy=accuracy,
        num_epochs=epochs
    )
```

## Workflow Definition

### Basic Workflow

```python
from flytekit import task, workflow

@task
def step1(x: int) -> int:
    return x + 1

@task
def step2(x: int) -> int:
    return x * 2

@workflow
def my_workflow(input_value: int) -> int:
    """
    A workflow connects tasks in a DAG.

    - Tasks execute in dependency order
    - Outputs flow between tasks automatically
    - Type checking at workflow definition time
    """
    a = step1(x=input_value)
    b = step2(x=a)
    return b
```

### Parallel Execution

```python
from flytekit import task, workflow
from typing import List

@task
def process_chunk(data: str) -> str:
    return f"processed_{data}"

@task
def aggregate_results(results: List[str]) -> str:
    return ",".join(results)

@workflow
def parallel_workflow(chunks: List[str]) -> str:
    """Tasks with no dependencies run in parallel."""
    # These run in parallel
    processed = [process_chunk(data=chunk) for chunk in chunks]

    # This waits for all parallel tasks
    final = aggregate_results(results=processed)
    return final
```

### Conditional Execution

```python
from flytekit import task, workflow, conditional

@task
def check_quality(data_path: str) -> float:
    # Return quality score
    return 0.95

@task
def full_training(data_path: str) -> str:
    return "full_model.pkl"

@task
def quick_training(data_path: str) -> str:
    return "quick_model.pkl"

@workflow
def conditional_workflow(data_path: str) -> str:
    """Choose path based on condition."""
    quality = check_quality(data_path=data_path)

    model_path = conditional("quality_check").if_(
        quality >= 0.9
    ).then(
        full_training(data_path=data_path)
    ).else_().then(
        quick_training(data_path=data_path)
    )

    return model_path
```

## Type System

### Supported Types

| Python Type | Flyte Type |
|-------------|------------|
| `int` | Integer |
| `float` | Float |
| `str` | String |
| `bool` | Boolean |
| `List[T]` | Collection |
| `Dict[K, V]` | Map |
| `datetime` | Datetime |
| `NamedTuple` | Struct |

### Using DataFrames

```python
from flytekit import task
import pandas as pd
from flytekit.types.structured import StructuredDataset

@task
def create_dataframe() -> StructuredDataset:
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"]
    })
    return StructuredDataset(dataframe=df)

@task
def process_dataframe(data: StructuredDataset) -> int:
    df = data.open(pd.DataFrame).all()
    return len(df)
```

### Using Files

```python
from flytekit import task
from flytekit.types.file import FlyteFile

@task
def create_file() -> FlyteFile:
    path = "/tmp/output.txt"
    with open(path, "w") as f:
        f.write("Hello, World!")
    return FlyteFile(path=path)

@task
def read_file(file: FlyteFile) -> str:
    with open(file, "r") as f:
        return f.read()
```

### Using Directories

```python
from flytekit import task
from flytekit.types.directory import FlyteDirectory

@task
def create_directory() -> FlyteDirectory:
    import os
    path = "/tmp/output_dir"
    os.makedirs(path, exist_ok=True)
    # Create files in directory
    return FlyteDirectory(path=path)

@task
def process_directory(directory: FlyteDirectory) -> int:
    import os
    files = os.listdir(directory)
    return len(files)
```

## Resource Configuration

### Task Resources

```python
from flytekit import task, Resources

@task(
    requests=Resources(cpu="2", mem="4Gi"),
    limits=Resources(cpu="4", mem="8Gi")
)
def resource_intensive_task(data: str) -> str:
    # This task gets 2-4 CPUs and 4-8GB memory
    return process(data)
```

### GPU Tasks

```python
from flytekit import task, Resources

@task(
    requests=Resources(cpu="4", mem="16Gi", gpu="1"),
    limits=Resources(cpu="8", mem="32Gi", gpu="1")
)
def gpu_training_task(data_path: str) -> str:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Training with GPU
    return "model.pt"
```

### Timeouts and Retries

```python
from flytekit import task
from datetime import timedelta

@task(
    timeout=timedelta(hours=2),
    retries=3
)
def long_running_task(data: str) -> str:
    """
    - Timeout: Task fails if running > 2 hours
    - Retries: Automatically retry up to 3 times on failure
    """
    return process(data)
```

## Environment Configuration

### Task with Specific Environment

```python
from flytekit import task, ImageSpec

# Define custom image
custom_image = ImageSpec(
    name="my-ml-image",
    packages=["scikit-learn==1.0", "pandas==2.0"],
    python_version="3.10"
)

@task(container_image=custom_image)
def ml_task(data: str) -> str:
    from sklearn.ensemble import RandomForestClassifier
    # Use scikit-learn from custom image
    return "result"
```

### Different Environments per Task

```python
from flytekit import task, workflow, ImageSpec

preprocessing_image = ImageSpec(
    name="preprocessing",
    packages=["pandas", "pyarrow"]
)

training_image = ImageSpec(
    name="training",
    packages=["torch", "transformers"]
)

@task(container_image=preprocessing_image)
def preprocess(data_path: str) -> str:
    import pandas as pd
    return "processed.parquet"

@task(container_image=training_image)
def train(data_path: str) -> str:
    import torch
    return "model.pt"

@workflow
def pipeline(input_path: str) -> str:
    processed = preprocess(data_path=input_path)
    model = train(data_path=processed)
    return model
```

## Error Handling

### Task-Level Error Handling

```python
from flytekit import task

@task
def safe_task(data: str) -> str:
    try:
        result = risky_operation(data)
        return result
    except ValueError as e:
        # Log and re-raise for Flyte to handle
        print(f"Error processing data: {e}")
        raise
```

### Workflow-Level Error Handling

```python
from flytekit import task, workflow
from flytekit.exceptions.user import FlyteRecoverableException

@task
def potentially_failing_task(data: str) -> str:
    if should_retry():
        # Raise recoverable exception for automatic retry
        raise FlyteRecoverableException("Temporary failure")
    return process(data)
```

## Caching

### Enable Task Caching

```python
from flytekit import task, HashMethod
from datetime import timedelta

@task(
    cache=True,
    cache_version="1.0",
    cache_serialize=True
)
def expensive_computation(data: str) -> str:
    """
    - cache=True: Enable caching
    - cache_version: Invalidate cache when changed
    - cache_serialize: Ensure only one execution runs
    """
    return expensive_process(data)
```

### Cache Key Customization

```python
from flytekit import task

@task(cache=True, cache_version="2.0")
def cached_task(data: str, config: dict) -> str:
    """
    Cache key is based on:
    - Task name
    - Cache version
    - Input values (data, config)
    """
    return process(data, config)
```

## Scheduling

### Cron Schedule

```python
from flytekit import workflow, LaunchPlan, CronSchedule

@workflow
def daily_pipeline(date: str) -> str:
    return process(date)

# Run every day at midnight
daily_schedule = LaunchPlan.create(
    "daily_pipeline_lp",
    daily_pipeline,
    schedule=CronSchedule(
        schedule="0 0 * * *"  # Cron syntax
    ),
    default_inputs={"date": "{{.scheduledTime}}"}
)
```

### Fixed Rate Schedule

```python
from flytekit import workflow, LaunchPlan, FixedRate
from datetime import timedelta

@workflow
def hourly_pipeline() -> str:
    return run_hourly_job()

hourly_schedule = LaunchPlan.create(
    "hourly_pipeline_lp",
    hourly_pipeline,
    schedule=FixedRate(duration=timedelta(hours=1))
)
```

## Testing Flows

### Local Execution

```python
# Run workflow locally
result = my_workflow(input_value=10)
print(f"Result: {result}")
```

### Unit Testing Tasks

```python
import pytest

def test_my_task():
    result = my_task(input_value=5)
    assert result == 10

def test_my_workflow():
    result = my_workflow(input_value=5)
    assert result == 12  # (5+1)*2
```

## Best Practices

### 1. Keep Tasks Small and Focused

```python
# Good: Single responsibility
@task
def load_data(path: str) -> StructuredDataset:
    pass

@task
def clean_data(data: StructuredDataset) -> StructuredDataset:
    pass

# Bad: Too much in one task
@task
def load_clean_transform_train(path: str) -> str:
    pass
```

### 2. Use Strong Typing

```python
# Good: Explicit types
@task
def process(data: List[float]) -> Dict[str, float]:
    pass

# Bad: No type hints
@task
def process(data):  # Missing types
    pass
```

### 3. Make Tasks Idempotent

```python
# Good: Same input = same output
@task
def transform(data: str) -> str:
    return data.upper()

# Bad: Side effects
counter = 0
@task
def increment(x: int) -> int:
    global counter
    counter += 1  # State changes between runs!
    return x + counter
```
