# Deploying Model API Endpoints

This guide covers creating and managing model API endpoints in Domino Data Lab.

## Environment Requirements

**Important:** Model APIs use the **default environment** set for your project. Ensure your environment has the `uwsgi` package installed.

```dockerfile
# Add to your environment's Dockerfile instructions
RUN pip install uwsgi
```

To set the default environment:
1. Go to **Project Settings** → **Execution Preferences**
2. Set the **Default Environment** to one with `uwsgi` installed

## Creating an Endpoint

### Endpoint Function Requirements

```python
# model.py
def predict(input_data):
    """
    Requirements:
    1. Function must be importable (in .py file at project root)
    2. Can have any name (configured in UI)
    3. Takes one argument (the request data)
    4. Returns JSON-serializable data
    """
    # Your prediction logic
    return {"result": "value"}
```

### Basic Endpoint Example

```python
# model.py
import pickle
import os

# Global model cache
_model = None

def load_model():
    """Load model once and cache."""
    global _model
    if _model is None:
        model_path = os.environ.get('MODEL_PATH', 'model.pkl')
        with open(model_path, 'rb') as f:
            _model = pickle.load(f)
    return _model

def predict(features):
    """
    Predict endpoint function.

    Args:
        features: List of feature values or dict with features

    Returns:
        Dict with prediction and confidence
    """
    model = load_model()

    # Handle different input formats
    if isinstance(features, dict):
        feature_values = list(features.values())
    elif isinstance(features, list):
        feature_values = features
    else:
        return {"error": "Invalid input format"}

    # Make prediction
    prediction = model.predict([feature_values])
    probability = model.predict_proba([feature_values])

    return {
        "prediction": int(prediction[0]),
        "confidence": float(max(probability[0])),
        "probabilities": probability[0].tolist()
    }
```

### Scikit-learn Example

```python
# model.py
import joblib
import numpy as np

_model = None

def load_model():
    global _model
    if _model is None:
        _model = joblib.load('random_forest_model.joblib')
    return _model

def predict(data):
    """
    Predict using scikit-learn model.

    Input format:
    {
        "features": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    }

    Output format:
    {
        "predictions": [0, 1],
        "model_version": "1.0"
    }
    """
    model = load_model()

    features = data.get('features', [])
    if not features:
        return {"error": "No features provided"}

    X = np.array(features)
    predictions = model.predict(X)

    return {
        "predictions": predictions.tolist(),
        "model_version": "1.0"
    }
```

### PyTorch Example

```python
# model.py
import torch
import json

_model = None
_device = None

def load_model():
    global _model, _device
    if _model is None:
        _device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        _model = torch.jit.load('model_scripted.pt')
        _model.to(_device)
        _model.eval()
    return _model, _device

def predict(data):
    """
    Predict using PyTorch model.

    Input format:
    {
        "inputs": [[1.0, 2.0, ...]]
    }
    """
    model, device = load_model()

    inputs = data.get('inputs', [])
    if not inputs:
        return {"error": "No inputs provided"}

    with torch.no_grad():
        tensor = torch.tensor(inputs, dtype=torch.float32).to(device)
        outputs = model(tensor)
        predictions = outputs.argmax(dim=1).cpu().tolist()

    return {"predictions": predictions}
```

### TensorFlow/Keras Example

```python
# model.py
import tensorflow as tf
import numpy as np
import os

_model = None

def load_model():
    global _model
    if _model is None:
        # Suppress TF warnings
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        _model = tf.keras.models.load_model('keras_model.h5')
    return _model

def predict(data):
    """
    Predict using TensorFlow/Keras model.
    """
    model = load_model()

    inputs = data.get('inputs', [])
    if not inputs:
        return {"error": "No inputs provided"}

    X = np.array(inputs)
    predictions = model.predict(X)

    return {
        "predictions": predictions.tolist(),
        "shape": list(predictions.shape)
    }
```

## Deploying via Domino UI

### Step-by-Step

1. Navigate to your project
2. Go to **Publish** → **Model APIs**
3. Click **+ New Model**
4. Fill in configuration:
   - **Name**: Descriptive name (e.g., `fraud-detector`)
   - **Description**: What the model does
   - **File**: Python file containing function (e.g., `model.py`)
   - **Function**: Function name (e.g., `predict`)
   - **Environment**: Select compute environment
   - **Hardware Tier**: Select resources (CPU/GPU)
5. Click **Publish**

### Environment Variables

Add environment variables in the UI:

```
MODEL_PATH=/mnt/artifacts/model.pkl
MODEL_VERSION=1.0
DEBUG=false
```

Access in code:
```python
import os
model_path = os.environ.get('MODEL_PATH', 'model.pkl')
```

## Deploying via API

### Using Domino Python Client

```python
from domino import Domino

domino = Domino(
    host="https://your-domino.com",
    api_key="your-api-key"
)

# Create model endpoint
model = domino.model_publish(
    file="model.py",
    function="predict",
    environment_id="env-123",
    name="my-classifier",
    description="Classification model"
)

print(f"Model ID: {model['id']}")
print(f"Model URL: {model['url']}")
```

## Calling Endpoints

Domino supports both synchronous (real-time) and asynchronous (long-running) request types.

### Synchronous Requests (Real-time)

For quick predictions that return immediately:

```python
import requests

# Synchronous endpoint URL format
url = "{DOMINO_URL}/models/{MODEL_ID}/latest/model"

# Authentication options:
# Option 1: Using auth parameter (token, token)
response = requests.post(
    url,
    auth=("{MODEL_ACCESS_TOKEN}", "{MODEL_ACCESS_TOKEN}"),
    json={"data": {"start": 1, "stop": 100}}
)

# Option 2: Using Bearer token in header
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_TOKEN"
}
response = requests.post(url, json={"data": {"features": [1.0, 2.0, 3.0]}}, headers=headers)

result = response.json()
print(result)
```

### Asynchronous Requests (Long-running)

For predictions that take longer to process:

```python
import requests
import time

DOMINO_URL = "https://your-domino.com"
MODEL_ID = "abc123"
MODEL_ACCESS_TOKEN = "your_token"

# Step 1: Submit async request
response = requests.post(
    f"{DOMINO_URL}/api/modelApis/async/v1/{MODEL_ID}",
    headers={
        "Authorization": f"Bearer {MODEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"parameters": {"input_file": "s3://example/filename.ext"}}
)

# Get prediction ID
prediction_id = response.json()["predictionId"]
print(f"Prediction ID: {prediction_id}")

# Step 2: Poll for results
while True:
    status_response = requests.get(
        f"{DOMINO_URL}/api/modelApis/async/v1/{MODEL_ID}/{prediction_id}",
        headers={"Authorization": f"Bearer {MODEL_ACCESS_TOKEN}"}
    )
    status = status_response.json()

    if status["status"] == "COMPLETED":
        print(f"Result: {status['result']}")
        break
    elif status["status"] == "FAILED":
        print(f"Error: {status['error']}")
        break
    else:
        print(f"Status: {status['status']}")
        time.sleep(5)  # Wait before polling again
```

### Request Parameter Formats

Depending on your function signature, format requests differently:

```python
# For function: my_function(x, y, z)
# Named parameters
{"data": {"x": 1, "y": 2, "z": 3}}
# Or positional
{"parameters": [1, 2, 3]}

# For function: my_function(dict)
{"parameters": [{"x": 1, "y": 2, "z": 3}]}

# For function: my_function(x, **kwargs)
{"data": {"x": 1, "y": 2, "z": 3}}
```

### JavaScript/React

```javascript
async function predict(features) {
    const response = await fetch(process.env.MODEL_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.MODEL_API_TOKEN}`,
        },
        body: JSON.stringify({ data: { features } }),
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return response.json();
}
```

### cURL

```bash
curl -X POST \
  "https://your-domino.com/models/abc123/latest/model" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"data": {"features": [1.0, 2.0, 3.0]}}'
```

## Version Management

### Creating New Version

1. Update your model file
2. Go to Model API → Versions
3. Click **+ New Version**
4. Select updated file/function
5. Publish

### Switching Active Version

```bash
# Use specific version
curl -X POST "https://domino.com/models/abc123/v/2/model" ...

# Use latest
curl -X POST "https://domino.com/models/abc123/latest/model" ...
```

### Blue-Green Deployment

1. Deploy new version as v2
2. Test v2 endpoint directly
3. Once validated, update clients to use v2
4. Deprecate v1

## Error Handling

### In Endpoint Function

```python
def predict(data):
    try:
        # Validate input
        if not data or 'features' not in data:
            return {
                "error": "Missing 'features' in input",
                "code": "INVALID_INPUT"
            }

        features = data['features']

        # Type checking
        if not isinstance(features, list):
            return {
                "error": "Features must be a list",
                "code": "TYPE_ERROR"
            }

        # Make prediction
        model = load_model()
        prediction = model.predict([features])

        return {"prediction": prediction.tolist()}

    except Exception as e:
        # Log error for debugging
        print(f"Prediction error: {str(e)}")
        return {
            "error": "Internal prediction error",
            "code": "PREDICTION_ERROR"
        }
```

### Client-Side Handling

```python
response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    result = response.json()
    if "error" in result:
        print(f"Model error: {result['error']}")
    else:
        print(f"Prediction: {result['prediction']}")
elif response.status_code == 401:
    print("Authentication failed")
elif response.status_code == 503:
    print("Model temporarily unavailable")
else:
    print(f"Request failed: {response.status_code}")
```

## Best Practices

### 1. Cache Model Loading

```python
# Good: Load once
_model = None
def load_model():
    global _model
    if _model is None:
        _model = load_from_disk()
    return _model

# Bad: Load every request
def predict(data):
    model = load_from_disk()  # Slow!
```

### 2. Input Validation

```python
def predict(data):
    # Validate early
    if not isinstance(data, dict):
        return {"error": "Input must be a dictionary"}

    features = data.get('features')
    if features is None:
        return {"error": "Missing 'features' key"}

    if len(features) != 4:
        return {"error": f"Expected 4 features, got {len(features)}"}
```

### 3. Response Consistency

```python
# Always return consistent structure
def predict(data):
    try:
        result = model.predict(data['features'])
        return {
            "success": True,
            "prediction": result,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "prediction": None,
            "error": str(e)
        }
```

### 4. Log for Debugging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict(data):
    logger.info(f"Received request: {data}")

    result = model.predict(data['features'])

    logger.info(f"Prediction: {result}")
    return {"prediction": result}
```
