---
name: domino-model-endpoints
description: Deploy and monitor model API endpoints in Domino. Covers creating prediction endpoints, version management, Grafana dashboards for latency/errors/resources, alerting, and GPU inference with NVIDIA Triton. Use when deploying models as APIs, monitoring production endpoints, or debugging endpoint issues.
---

# Domino Model Endpoints Skill

This skill provides comprehensive knowledge for deploying and monitoring model API endpoints in Domino Data Lab.

## Key Concepts

### Model Endpoints Overview

Domino Model Endpoints provide:
- REST API for model predictions
- Automatic scaling and load balancing
- Version management
- Built-in monitoring with Grafana
- Authentication via API tokens

### Endpoint Lifecycle

```
Train Model → Register → Deploy Endpoint → Monitor → Update Version
```

## Related Documentation

- [DEPLOY-ENDPOINT.md](./DEPLOY-ENDPOINT.md) - Creating model APIs
- [MONITORING.md](./MONITORING.md) - Grafana, metrics, alerts
- [SCALING.md](./SCALING.md) - GPU inference, Triton, scaling

## Environment Requirements

**Important:** Model APIs use the **default environment** set for your project. The environment must have the `uwsgi` Python package installed for model endpoints to work.

### Required Package
```dockerfile
# Add to your environment's Dockerfile instructions
RUN pip install uwsgi
```

Or in requirements.txt:
```
uwsgi
```

### Setting Default Environment
1. Go to **Project Settings** → **Execution Preferences**
2. Set the **Default Environment** that includes `uwsgi`
3. This environment will be used for all Model API deployments

## Quick Start

### 1. Create Endpoint Function

```python
# model.py
def predict(features):
    """
    Domino calls this function for predictions.

    Args:
        features: Input data (dict, list, or primitive)

    Returns:
        JSON-serializable prediction result
    """
    import pickle

    # Load model (cached after first call)
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)

    prediction = model.predict([features])
    return {"prediction": prediction.tolist()}
```

### 2. Deploy via Domino UI

1. Go to **Publish** → **Model APIs**
2. Click **New Model**
3. Configure:
   - Name: `my-classifier`
   - File: `model.py`
   - Function: `predict`
   - Environment: Select compute environment
4. Click **Publish**

### 3. Call the Endpoint

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"data": {"features": [1.0, 2.0, 3.0]}}' \
  https://your-domino.com/models/abc123/latest/model
```

## Environment Variables

When calling endpoints from apps:

| Variable | Description |
|----------|-------------|
| `MODEL_API_URL` | Full endpoint URL |
| `MODEL_API_TOKEN` | Bearer token for authentication |

## Key Metrics to Monitor

| Metric | Target |
|--------|--------|
| Latency P50 | < 100ms |
| Latency P99 | < 500ms |
| Error Rate | < 1% |
| CPU Usage | < 80% |
| Memory | Stable (no growth) |

## Documentation Links

- Domino Model APIs: https://docs.dominodatalab.com/en/latest/user_guide/8dbc91/model-apis/
