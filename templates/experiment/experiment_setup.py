"""
Domino Experiment Tracking Setup

This module provides utilities for setting up MLflow experiment tracking
in Domino Data Lab with proper naming conventions and context logging.

Usage:
    from experiment_setup import setup_experiment, log_domino_context, setup_autolog

    setup_experiment("my-model")
    setup_autolog()

    with mlflow.start_run(run_name="training-v1"):
        log_domino_context()
        # Your training code here
"""

import mlflow
import os


def setup_experiment(base_name: str = "experiment") -> str:
    """
    Set up a Domino-compatible MLflow experiment.

    IMPORTANT: Experiment names must be unique across the entire Domino
    deployment, not just your project. This function automatically appends
    username and project name to ensure uniqueness.

    Args:
        base_name: Base name for the experiment

    Returns:
        The full experiment name
    """
    username = os.environ.get('DOMINO_STARTING_USERNAME', 'unknown')
    project = os.environ.get('DOMINO_PROJECT_NAME', 'unknown')

    # Create unique experiment name
    experiment_name = f"{base_name}-{project}-{username}"

    mlflow.set_experiment(experiment_name)
    print(f"Experiment set: {experiment_name}")

    return experiment_name


def log_domino_context():
    """
    Log Domino environment information as MLflow tags.

    Call this at the start of each run to capture:
    - User who started the run
    - Project name
    - Domino run ID
    - Hardware tier used
    """
    mlflow.set_tags({
        "domino.user": os.environ.get('DOMINO_STARTING_USERNAME', 'unknown'),
        "domino.project": os.environ.get('DOMINO_PROJECT_NAME', 'unknown'),
        "domino.run_id": os.environ.get('DOMINO_RUN_ID', 'unknown'),
        "domino.hardware_tier": os.environ.get('DOMINO_HARDWARE_TIER_NAME', 'unknown'),
    })


def setup_autolog():
    """
    Enable MLflow auto-logging for detected ML frameworks.

    Automatically detects and enables logging for:
    - scikit-learn
    - TensorFlow/Keras
    - PyTorch
    - XGBoost
    - LightGBM
    """
    try:
        import sklearn
        mlflow.sklearn.autolog()
        print("Enabled scikit-learn auto-logging")
    except ImportError:
        pass

    try:
        import tensorflow
        mlflow.tensorflow.autolog()
        print("Enabled TensorFlow auto-logging")
    except ImportError:
        pass

    try:
        import torch
        mlflow.pytorch.autolog()
        print("Enabled PyTorch auto-logging")
    except ImportError:
        pass

    try:
        import xgboost
        mlflow.xgboost.autolog()
        print("Enabled XGBoost auto-logging")
    except ImportError:
        pass

    try:
        import lightgbm
        mlflow.lightgbm.autolog()
        print("Enabled LightGBM auto-logging")
    except ImportError:
        pass


def enable_large_artifact_upload():
    """
    Enable multipart upload for large artifacts.

    Call this before logging large files (e.g., LLMs, deep learning models)
    to enable chunked upload and prevent timeouts.
    """
    os.environ['MLFLOW_ENABLE_PROXY_MULTIPART_UPLOAD'] = "true"
    os.environ['MLFLOW_MULTIPART_UPLOAD_CHUNK_SIZE'] = "104857600"  # 100MB
    print("Enabled multipart upload for large artifacts")


# Example usage
if __name__ == "__main__":
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    # Setup
    setup_experiment("iris-example")
    setup_autolog()

    # Load data
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42
    )

    # Train with MLflow tracking
    with mlflow.start_run(run_name="example-run"):
        log_domino_context()

        # Train model (auto-logged)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Custom metrics
        accuracy = model.score(X_test, y_test)
        mlflow.log_metric("test_accuracy", accuracy)

        print(f"Test accuracy: {accuracy:.4f}")
        print(f"Run ID: {mlflow.active_run().info.run_id}")
