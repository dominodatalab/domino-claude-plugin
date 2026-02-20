# Domino Flows Examples

This guide provides complete, production-ready flow examples for common ML workflows.

## Example 1: Data Processing Pipeline

### Use Case

ETL pipeline that loads raw data, cleans it, and creates features.

```python
from flytekit import task, workflow, Resources
from flytekit.types.structured import StructuredDataset
from flytekit.types.file import FlyteFile
from typing import NamedTuple
import pandas as pd

class DataStats(NamedTuple):
    num_rows: int
    num_cols: int
    null_percentage: float

@task(
    requests=Resources(cpu="2", mem="4Gi"),
    cache=True,
    cache_version="1.0"
)
def load_raw_data(source_path: str) -> StructuredDataset:
    """Load raw data from source."""
    df = pd.read_csv(source_path)
    return StructuredDataset(dataframe=df)

@task(requests=Resources(cpu="2", mem="4Gi"))
def validate_data(data: StructuredDataset) -> DataStats:
    """Validate data quality."""
    df = data.open(pd.DataFrame).all()

    stats = DataStats(
        num_rows=len(df),
        num_cols=len(df.columns),
        null_percentage=df.isnull().sum().sum() / df.size * 100
    )

    if stats.null_percentage > 50:
        raise ValueError(f"Too many null values: {stats.null_percentage}%")

    return stats

@task(requests=Resources(cpu="4", mem="8Gi"))
def clean_data(data: StructuredDataset) -> StructuredDataset:
    """Clean and impute missing values."""
    df = data.open(pd.DataFrame).all()

    # Drop duplicates
    df = df.drop_duplicates()

    # Impute missing values
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    categorical_cols = df.select_dtypes(include=['object']).columns
    df[categorical_cols] = df[categorical_cols].fillna('unknown')

    return StructuredDataset(dataframe=df)

@task(requests=Resources(cpu="4", mem="8Gi"))
def create_features(data: StructuredDataset) -> StructuredDataset:
    """Engineer features from clean data."""
    df = data.open(pd.DataFrame).all()

    # Example feature engineering
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month

    return StructuredDataset(dataframe=df)

@task
def save_processed_data(
    data: StructuredDataset,
    output_path: str
) -> str:
    """Save processed data."""
    df = data.open(pd.DataFrame).all()
    df.to_parquet(output_path, index=False)
    return output_path

@workflow
def data_processing_pipeline(
    source_path: str,
    output_path: str
) -> str:
    """Complete data processing pipeline."""
    raw_data = load_raw_data(source_path=source_path)
    stats = validate_data(data=raw_data)
    clean = clean_data(data=raw_data)
    features = create_features(data=clean)
    final_path = save_processed_data(data=features, output_path=output_path)
    return final_path
```

## Example 2: Model Training Pipeline

### Use Case

Train, evaluate, and register a machine learning model.

```python
from flytekit import task, workflow, Resources
from flytekit.types.file import FlyteFile
from flytekit.types.structured import StructuredDataset
from typing import NamedTuple, Tuple
import mlflow

class TrainingResults(NamedTuple):
    model_path: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float

@task(requests=Resources(cpu="2", mem="4Gi"))
def split_data(
    data: StructuredDataset,
    test_size: float = 0.2
) -> Tuple[StructuredDataset, StructuredDataset]:
    """Split data into train and test sets."""
    import pandas as pd
    from sklearn.model_selection import train_test_split

    df = data.open(pd.DataFrame).all()
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=42)

    return (
        StructuredDataset(dataframe=train_df),
        StructuredDataset(dataframe=test_df)
    )

@task(
    requests=Resources(cpu="4", mem="8Gi", gpu="1"),
    timeout=timedelta(hours=4),
    retries=2
)
def train_model(
    train_data: StructuredDataset,
    target_column: str,
    model_type: str = "random_forest"
) -> FlyteFile:
    """Train ML model."""
    import pandas as pd
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    df = train_data.open(pd.DataFrame).all()
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Select model
    if model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    else:
        model = LogisticRegression(random_state=42)

    # Train
    model.fit(X, y)

    # Save model
    model_path = "/tmp/model.joblib"
    joblib.dump(model, model_path)

    return FlyteFile(path=model_path)

@task(requests=Resources(cpu="2", mem="4Gi"))
def evaluate_model(
    model_file: FlyteFile,
    test_data: StructuredDataset,
    target_column: str
) -> TrainingResults:
    """Evaluate model performance."""
    import pandas as pd
    import joblib
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    # Load model
    model = joblib.load(model_file)

    # Prepare test data
    df = test_data.open(pd.DataFrame).all()
    X_test = df.drop(columns=[target_column])
    y_test = df[target_column]

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics
    results = TrainingResults(
        model_path=str(model_file),
        accuracy=accuracy_score(y_test, y_pred),
        precision=precision_score(y_test, y_pred, average='weighted'),
        recall=recall_score(y_test, y_pred, average='weighted'),
        f1_score=f1_score(y_test, y_pred, average='weighted')
    )

    return results

@task
def register_model(
    model_file: FlyteFile,
    results: TrainingResults,
    model_name: str
) -> str:
    """Register model if performance is acceptable."""
    import mlflow

    if results.accuracy < 0.8:
        print(f"Model accuracy {results.accuracy} below threshold, not registering")
        return "not_registered"

    with mlflow.start_run():
        mlflow.log_metrics({
            "accuracy": results.accuracy,
            "precision": results.precision,
            "recall": results.recall,
            "f1_score": results.f1_score
        })

        mlflow.sklearn.log_model(
            sk_model=joblib.load(model_file),
            artifact_path="model",
            registered_model_name=model_name
        )

    return f"registered:{model_name}"

@workflow
def model_training_pipeline(
    data: StructuredDataset,
    target_column: str,
    model_name: str,
    model_type: str = "random_forest"
) -> str:
    """Complete model training pipeline."""
    train_data, test_data = split_data(data=data)

    model_file = train_model(
        train_data=train_data,
        target_column=target_column,
        model_type=model_type
    )

    results = evaluate_model(
        model_file=model_file,
        test_data=test_data,
        target_column=target_column
    )

    registration_status = register_model(
        model_file=model_file,
        results=results,
        model_name=model_name
    )

    return registration_status
```

## Example 3: Batch Inference Pipeline

### Use Case

Run predictions on a large dataset in parallel batches.

```python
from flytekit import task, workflow, dynamic, Resources
from flytekit.types.structured import StructuredDataset
from flytekit.types.file import FlyteFile
from typing import List
import pandas as pd

@task
def load_model(model_path: str) -> FlyteFile:
    """Load model from registry or path."""
    return FlyteFile(path=model_path)

@task
def split_into_batches(
    data: StructuredDataset,
    batch_size: int
) -> List[StructuredDataset]:
    """Split data into batches for parallel processing."""
    df = data.open(pd.DataFrame).all()

    batches = []
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        batches.append(StructuredDataset(dataframe=batch_df))

    return batches

@task(requests=Resources(cpu="2", mem="4Gi"))
def predict_batch(
    model_file: FlyteFile,
    batch: StructuredDataset
) -> StructuredDataset:
    """Run predictions on a single batch."""
    import joblib

    model = joblib.load(model_file)
    df = batch.open(pd.DataFrame).all()

    predictions = model.predict(df)
    df['prediction'] = predictions

    return StructuredDataset(dataframe=df)

@task
def combine_results(
    results: List[StructuredDataset]
) -> StructuredDataset:
    """Combine all batch results."""
    dfs = [r.open(pd.DataFrame).all() for r in results]
    combined = pd.concat(dfs, ignore_index=True)
    return StructuredDataset(dataframe=combined)

@dynamic
def parallel_inference(
    model_file: FlyteFile,
    batches: List[StructuredDataset]
) -> List[StructuredDataset]:
    """Run inference on batches in parallel using dynamic task."""
    results = []
    for batch in batches:
        result = predict_batch(model_file=model_file, batch=batch)
        results.append(result)
    return results

@workflow
def batch_inference_pipeline(
    data: StructuredDataset,
    model_path: str,
    batch_size: int = 1000
) -> StructuredDataset:
    """Complete batch inference pipeline."""
    model = load_model(model_path=model_path)
    batches = split_into_batches(data=data, batch_size=batch_size)
    results = parallel_inference(model_file=model, batches=batches)
    final = combine_results(results=results)
    return final
```

## Example 4: Retraining Pipeline with Data Drift Detection

### Use Case

Automatically retrain model when data drift is detected.

```python
from flytekit import task, workflow, conditional, Resources
from flytekit.types.structured import StructuredDataset
from flytekit.types.file import FlyteFile
from typing import NamedTuple
from datetime import timedelta

class DriftReport(NamedTuple):
    drift_detected: bool
    drift_score: float
    features_drifted: list

@task
def load_reference_data(path: str) -> StructuredDataset:
    """Load reference (training) data distribution."""
    import pandas as pd
    return StructuredDataset(dataframe=pd.read_parquet(path))

@task
def load_current_data(path: str) -> StructuredDataset:
    """Load current (production) data."""
    import pandas as pd
    return StructuredDataset(dataframe=pd.read_parquet(path))

@task
def detect_drift(
    reference: StructuredDataset,
    current: StructuredDataset,
    threshold: float = 0.1
) -> DriftReport:
    """Detect data drift using statistical tests."""
    from scipy import stats
    import pandas as pd

    ref_df = reference.open(pd.DataFrame).all()
    cur_df = current.open(pd.DataFrame).all()

    features_drifted = []
    drift_scores = []

    for col in ref_df.select_dtypes(include=['number']).columns:
        if col in cur_df.columns:
            stat, p_value = stats.ks_2samp(ref_df[col], cur_df[col])
            drift_scores.append(stat)
            if p_value < 0.05:
                features_drifted.append(col)

    avg_drift = sum(drift_scores) / len(drift_scores) if drift_scores else 0

    return DriftReport(
        drift_detected=avg_drift > threshold,
        drift_score=avg_drift,
        features_drifted=features_drifted
    )

@task
def send_drift_alert(report: DriftReport) -> str:
    """Send alert about drift detection."""
    print(f"Drift detected! Score: {report.drift_score}")
    print(f"Features affected: {report.features_drifted}")
    # In production: send email, Slack message, etc.
    return "alert_sent"

@task(
    requests=Resources(cpu="4", mem="8Gi"),
    timeout=timedelta(hours=2)
)
def retrain_model(
    data: StructuredDataset,
    target_column: str
) -> FlyteFile:
    """Retrain model with new data."""
    import pandas as pd
    import joblib
    from sklearn.ensemble import RandomForestClassifier

    df = data.open(pd.DataFrame).all()
    X = df.drop(columns=[target_column])
    y = df[target_column]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    model_path = "/tmp/retrained_model.joblib"
    joblib.dump(model, model_path)

    return FlyteFile(path=model_path)

@task
def skip_retraining() -> str:
    """No retraining needed."""
    return "no_drift_detected"

@workflow
def drift_monitoring_pipeline(
    reference_path: str,
    current_path: str,
    target_column: str,
    drift_threshold: float = 0.1
) -> str:
    """Monitor for drift and retrain if needed."""
    reference = load_reference_data(path=reference_path)
    current = load_current_data(path=current_path)

    report = detect_drift(
        reference=reference,
        current=current,
        threshold=drift_threshold
    )

    result = conditional("drift_check").if_(
        report.drift_detected == True
    ).then(
        retrain_model(data=current, target_column=target_column)
    ).else_().then(
        skip_retraining()
    )

    # Always send alert if drift detected
    send_drift_alert(report=report)

    return str(result)
```

## Example 5: Multi-Model Ensemble Pipeline

### Use Case

Train multiple models and combine them into an ensemble.

```python
from flytekit import task, workflow, dynamic, Resources
from flytekit.types.file import FlyteFile
from flytekit.types.structured import StructuredDataset
from typing import List, NamedTuple
import pandas as pd

class ModelResult(NamedTuple):
    model_file: FlyteFile
    model_type: str
    accuracy: float

@task(requests=Resources(cpu="2", mem="4Gi"))
def train_random_forest(
    train_data: StructuredDataset,
    target_column: str
) -> ModelResult:
    """Train Random Forest model."""
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score

    df = train_data.open(pd.DataFrame).all()
    X = df.drop(columns=[target_column])
    y = df[target_column]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    scores = cross_val_score(model, X, y, cv=5)
    model.fit(X, y)

    path = "/tmp/random_forest.joblib"
    joblib.dump(model, path)

    return ModelResult(
        model_file=FlyteFile(path=path),
        model_type="random_forest",
        accuracy=scores.mean()
    )

@task(requests=Resources(cpu="2", mem="4Gi"))
def train_gradient_boosting(
    train_data: StructuredDataset,
    target_column: str
) -> ModelResult:
    """Train Gradient Boosting model."""
    import joblib
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score

    df = train_data.open(pd.DataFrame).all()
    X = df.drop(columns=[target_column])
    y = df[target_column]

    model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    scores = cross_val_score(model, X, y, cv=5)
    model.fit(X, y)

    path = "/tmp/gradient_boosting.joblib"
    joblib.dump(model, path)

    return ModelResult(
        model_file=FlyteFile(path=path),
        model_type="gradient_boosting",
        accuracy=scores.mean()
    )

@task(requests=Resources(cpu="2", mem="4Gi"))
def train_logistic_regression(
    train_data: StructuredDataset,
    target_column: str
) -> ModelResult:
    """Train Logistic Regression model."""
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    df = train_data.open(pd.DataFrame).all()
    X = df.drop(columns=[target_column])
    y = df[target_column]

    model = LogisticRegression(random_state=42, max_iter=1000)
    scores = cross_val_score(model, X, y, cv=5)
    model.fit(X, y)

    path = "/tmp/logistic_regression.joblib"
    joblib.dump(model, path)

    return ModelResult(
        model_file=FlyteFile(path=path),
        model_type="logistic_regression",
        accuracy=scores.mean()
    )

@task
def create_ensemble(
    models: List[ModelResult],
    weights: str = "equal"
) -> FlyteFile:
    """Create ensemble from trained models."""
    import joblib
    from sklearn.ensemble import VotingClassifier

    # Load all models
    estimators = []
    for m in models:
        model = joblib.load(m.model_file)
        estimators.append((m.model_type, model))

    # Create voting ensemble
    if weights == "accuracy":
        model_weights = [m.accuracy for m in models]
    else:
        model_weights = None

    ensemble = VotingClassifier(
        estimators=estimators,
        voting='soft',
        weights=model_weights
    )

    path = "/tmp/ensemble.joblib"
    joblib.dump(ensemble, path)

    return FlyteFile(path=path)

@workflow
def ensemble_pipeline(
    train_data: StructuredDataset,
    target_column: str
) -> FlyteFile:
    """Train multiple models and create ensemble."""
    # Train models in parallel
    rf_result = train_random_forest(
        train_data=train_data,
        target_column=target_column
    )
    gb_result = train_gradient_boosting(
        train_data=train_data,
        target_column=target_column
    )
    lr_result = train_logistic_regression(
        train_data=train_data,
        target_column=target_column
    )

    # Create ensemble
    ensemble = create_ensemble(
        models=[rf_result, gb_result, lr_result],
        weights="accuracy"
    )

    return ensemble
```

## Running Examples

### Local Execution

```python
# Test locally
from flytekit.configuration import Config

if __name__ == "__main__":
    # Run workflow locally
    result = data_processing_pipeline(
        source_path="data/raw.csv",
        output_path="data/processed.parquet"
    )
    print(f"Result: {result}")
```

### Register and Run on Domino

```bash
# Package and register workflows
pyflyte register workflows/

# Run via Domino UI or CLI
```
