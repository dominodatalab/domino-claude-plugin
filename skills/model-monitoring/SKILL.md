---
name: domino-model-monitoring
description: Monitor deployed models in Domino including drift detection, model quality tracking, and alerting. Covers data drift analysis, prediction capture, baseline comparison, alert configuration, and remediation workflows. Use when monitoring production models, detecting drift, or setting up model health alerts.
---

# Domino Model Monitoring Skill

## Description
This skill helps users monitor deployed models in Domino, including drift detection, model quality tracking, and alerting.

## Activation
Activate this skill when users want to:
- Monitor deployed model performance
- Set up drift detection
- Configure monitoring alerts
- Analyze prediction data
- Understand model degradation

## What is Model Monitoring?

Domino Model Monitoring provides:
- **Data Drift Detection**: Detect changes in input data distributions
- **Model Quality Tracking**: Monitor prediction accuracy over time
- **Alerting**: Get notified when metrics exceed thresholds
- **Prediction Capture**: Log predictions for analysis
- **Reproducibility**: Diagnose issues with captured data

## Setting Up Monitoring

### Prerequisites
1. Deployed Model API in Domino
2. Training dataset (for baseline)
3. Ground truth data (optional, for quality metrics)

### Enable Monitoring
1. Go to your Model API page
2. Click **Monitoring** tab
3. Click **Set Up Monitoring**
4. Upload training dataset
5. Configure drift detection settings

### Register Training Data
```python
# Training data provides baseline for drift detection
# Upload via UI or programmatically

import pandas as pd

# Your training data
train_df = pd.read_csv("training_data.csv")

# Save for monitoring setup
train_df.to_csv("/mnt/artifacts/training_data.csv", index=False)
```

## Drift Detection

### Types of Drift

| Drift Type | Description |
|------------|-------------|
| **Data Drift** | Input feature distributions change |
| **Concept Drift** | Relationship between inputs and outputs changes |
| **Prediction Drift** | Output distribution changes |

### Statistical Tests

Domino supports multiple drift detection tests:

| Test | Best For |
|------|----------|
| **Kullback-Leibler Divergence** | General-purpose, most common |
| **Population Stability Index (PSI)** | Finance industry standard |
| **Wasserstein Distance** | Comparing distributions |
| **Energy Distance** | Multivariate distributions |

### Configure Drift Detection

1. Go to Model API > **Monitoring**
2. Click **Configure Drift Detection**
3. For each feature:
   - Select test type
   - Set threshold
   - Enable/disable alerts

### Example Thresholds

| Test | Low Drift | Medium Drift | High Drift |
|------|-----------|--------------|------------|
| KL Divergence | < 0.1 | 0.1 - 0.2 | > 0.2 |
| PSI | < 0.1 | 0.1 - 0.25 | > 0.25 |

## Prediction Capture

### How It Works
Domino automatically captures predictions:
1. Model receives request
2. Prediction is made
3. Input/output logged to dataset
4. Data available for drift analysis

### Access Captured Data
```python
import pandas as pd

# Predictions captured in Domino Dataset
predictions_df = pd.read_parquet(
    "/mnt/data/model-predictions/predictions.parquet"
)

print(predictions_df.head())
```

### Capture Frequency
- Predictions batched hourly
- Full data available in monitoring dataset
- Retention configurable by admin

## Model Quality Monitoring

### With Ground Truth
If you provide ground truth labels:

```python
# Upload ground truth
ground_truth = pd.DataFrame({
    "prediction_id": [...],
    "actual_label": [...]
})

# Upload to monitoring
ground_truth.to_csv("/mnt/artifacts/ground_truth.csv", index=False)
```

### Quality Metrics
- Accuracy
- Precision/Recall
- F1 Score
- AUC-ROC
- Mean Squared Error (regression)

### Schedule Quality Checks
1. Go to Monitoring > **Quality**
2. Upload ground truth dataset
3. Configure metric thresholds
4. Set check frequency

## Alerting

### Configure Alerts
1. Go to Model API > **Monitoring**
2. Click **Alerts**
3. Configure:
   - Metric to monitor
   - Threshold
   - Alert recipients (email)

### Alert Types
- Drift threshold exceeded
- Quality metric below threshold
- Model API health issues
- Prediction volume anomalies

### Disable Noisy Alerts
Click the bell icon next to features to exclude from alerts.

## Viewing Monitoring Data

### Monitoring Dashboard
Go to Model API > **Monitoring** to see:
- Drift trends over time
- Feature distributions
- Quality metrics
- Alert history

### Export Data
```python
# Export monitoring data for custom analysis
import pandas as pd

drift_report = pd.read_csv("/mnt/data/monitoring/drift_report.csv")
print(drift_report)
```

## Responding to Drift

### Investigation Workflow
1. **Alert received**: Drift detected on feature X
2. **Investigate**: View feature distribution changes
3. **Diagnose**: Compare current vs training data
4. **Action**: Retrain or update model

### Retrain Model
```python
# When drift is detected, retrain with recent data
from sklearn.ensemble import RandomForestClassifier

# Load recent data
recent_data = pd.read_csv("/mnt/data/recent_predictions.csv")

# Combine with ground truth
training_data = merge_with_ground_truth(recent_data)

# Retrain
model = RandomForestClassifier()
model.fit(training_data[features], training_data[label])

# Deploy new version
joblib.dump(model, "/mnt/artifacts/model_v2.joblib")
```

### Automated Retraining
Set up scheduled job to retrain when drift detected:
```python
# scheduled_retrain.py
from domino import Domino

domino = Domino("project/model-project")

# Check drift status
drift_status = check_drift_metrics()

if drift_status["max_drift"] > 0.2:
    # Trigger retrain job
    domino.runs_start(
        command="python retrain.py",
        hardware_tier_name="medium"
    )
```

## Best Practices

### 1. Baseline with Quality Data
Use clean, representative training data for baseline.

### 2. Monitor Key Features
Focus on features with highest importance:
```python
# Identify important features
importances = model.feature_importances_
top_features = sorted(
    zip(feature_names, importances),
    key=lambda x: x[1],
    reverse=True
)[:10]
```

### 3. Set Appropriate Thresholds
- Start with conservative thresholds
- Adjust based on business impact
- Different thresholds for different features

### 4. Include Business Context
Not all drift requires action:
- Seasonal variations may be expected
- New customer segments may cause drift
- Consider business impact before reacting

### 5. Regular Reviews
Schedule periodic monitoring reviews:
- Weekly: Check drift trends
- Monthly: Review alert configurations
- Quarterly: Assess model performance

## Troubleshooting

### No Data in Monitoring
- Verify Model API is receiving traffic
- Check prediction capture is enabled
- Wait for hourly batch processing

### Drift Always High
- Review training data quality
- Check for data preprocessing differences
- Verify feature encoding consistency

### Alerts Not Sending
- Check email configuration
- Verify alert thresholds
- Review spam folders

## Documentation Reference
- [Drift detection for monitored models](https://docs.dominodatalab.com/en/latest/user_guide/86bc1f/drift-detection-for-monitored-models/)
- [Domino endpoint drift detection](https://docs.dominodatalab.com/en/latest/user_guide/c97091/domino-endpoint-drift-detection/)
- [Monitor workflows](https://docs.dominodatalab.com/en/latest/user_guide/85f76d/monitor-workflows/)
