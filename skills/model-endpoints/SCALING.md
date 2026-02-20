# Scaling Model Endpoints

This guide covers scaling strategies for Domino model endpoints, including GPU inference with NVIDIA Triton.

## Scaling Strategies

### Horizontal Scaling (Replicas)

Increase the number of model instances:

```
Traffic → Load Balancer → [Model Pod 1]
                       → [Model Pod 2]
                       → [Model Pod 3]
```

**When to use:**
- High request volume
- CPU-bound models
- Need high availability

### Vertical Scaling (Resources)

Increase CPU/memory per instance:

**When to use:**
- Large models
- Memory-intensive operations
- GPU requirements

## Configuring Replicas

### Via Domino UI

1. Go to Model API settings
2. Find **Scaling** section
3. Set **Minimum Replicas** and **Maximum Replicas**
4. Configure **Target CPU Utilization** for auto-scaling

### Replica Guidelines

| Traffic | Min Replicas | Max Replicas |
|---------|-------------|--------------|
| Low (< 10 RPS) | 1 | 2 |
| Medium (10-100 RPS) | 2 | 5 |
| High (> 100 RPS) | 3 | 10+ |

## Auto-Scaling

### CPU-Based Auto-Scaling

Domino automatically scales based on CPU utilization:

```yaml
autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

**How it works:**
1. Monitor average CPU across pods
2. If CPU > 70%, add pods
3. If CPU < 70%, remove pods (with cooldown)

### Memory-Based Considerations

- Memory doesn't trigger auto-scaling by default
- Set appropriate memory limits to prevent OOM
- Monitor memory for capacity planning

## Hardware Tiers

### Selecting Hardware

| Tier | Use Case |
|------|----------|
| small | Simple models, low traffic |
| medium | Standard ML models |
| large | Large models, high throughput |
| gpu-small | Small deep learning models |
| gpu-large | Large neural networks, LLMs |

### GPU Considerations

```python
# Check for GPU availability in your model
import torch

def load_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    model = MyModel().to(device)
    return model, device
```

## GPU Inference with NVIDIA Triton

### What is Triton?

NVIDIA Triton Inference Server provides:
- High-performance inference
- Multiple model support
- Dynamic batching
- Model versioning
- Metrics and monitoring

### Triton Model Repository Structure

```
model_repository/
└── my_model/
    ├── config.pbtxt
    └── 1/
        └── model.onnx
```

### config.pbtxt Example

```protobuf
name: "my_model"
platform: "onnxruntime_onnx"
max_batch_size: 8
input [
  {
    name: "input"
    data_type: TYPE_FP32
    dims: [ 224, 224, 3 ]
  }
]
output [
  {
    name: "output"
    data_type: TYPE_FP32
    dims: [ 1000 ]
  }
]
instance_group [
  {
    kind: KIND_GPU
    count: 1
  }
]
dynamic_batching {
  preferred_batch_size: [ 4, 8 ]
  max_queue_delay_microseconds: 100
}
```

### Converting Models for Triton

**PyTorch to ONNX:**
```python
import torch

model = MyModel()
model.eval()

dummy_input = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={'input': {0: 'batch_size'}}
)
```

**TensorFlow to SavedModel:**
```python
import tensorflow as tf

model = tf.keras.models.load_model('my_model.h5')
model.save('model_repository/my_model/1/model.savedmodel')
```

### Dynamic Batching

Group multiple requests for efficient GPU utilization:

```protobuf
dynamic_batching {
  preferred_batch_size: [ 4, 8, 16 ]
  max_queue_delay_microseconds: 100
}
```

**Benefits:**
- Higher GPU utilization
- Better throughput
- Lower cost per prediction

## Optimizing Model Performance

### Model Optimization Techniques

| Technique | Speedup | Accuracy Impact |
|-----------|---------|-----------------|
| Quantization (INT8) | 2-4x | Minimal |
| Pruning | 2-3x | Varies |
| Knowledge Distillation | 2-10x | Some |
| ONNX Runtime | 1.5-2x | None |

### Quantization Example

```python
import torch

# Dynamic quantization
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)
```

### ONNX Optimization

```python
import onnx
from onnxruntime.transformers import optimizer

# Optimize ONNX model
optimized_model = optimizer.optimize_model(
    "model.onnx",
    model_type='bert',
    num_heads=12,
    hidden_size=768
)
optimized_model.save_model_to_file("model_optimized.onnx")
```

## Caching Strategies

### In-Memory Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_predict(features_hash):
    """Cache predictions for repeated inputs."""
    features = decode_features(features_hash)
    return model.predict(features)

def predict(data):
    features = data['features']
    features_hash = hashlib.md5(str(features).encode()).hexdigest()
    return cached_predict(features_hash)
```

### External Caching (Redis)

```python
import redis
import json
import hashlib

redis_client = redis.Redis(host='redis-host', port=6379)
CACHE_TTL = 3600  # 1 hour

def predict(data):
    features = data['features']
    cache_key = f"pred:{hashlib.md5(str(features).encode()).hexdigest()}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Compute prediction
    result = model.predict(features)

    # Store in cache
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))

    return result
```

## Load Testing

### Using Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class ModelUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def predict(self):
        self.client.post(
            "/models/abc123/latest/model",
            json={"data": {"features": [1.0, 2.0, 3.0]}},
            headers={
                "Authorization": "Bearer TOKEN",
                "Content-Type": "application/json"
            }
        )
```

Run test:
```bash
locust -f locustfile.py --host=https://your-domino.com
```

### Performance Targets

| Metric | Development | Production |
|--------|-------------|------------|
| Latency P50 | < 200ms | < 100ms |
| Latency P99 | < 1s | < 500ms |
| Throughput | 10 RPS | 100+ RPS |
| Error Rate | < 5% | < 0.1% |

## Cost Optimization

### Right-Sizing Resources

1. Start with small hardware tier
2. Monitor CPU/memory utilization
3. Scale up only if needed
4. Use auto-scaling for variable traffic

### Spot/Preemptible Instances

For non-critical workloads:
- Lower cost
- May be interrupted
- Good for batch processing

### Idle Scaling

```yaml
# Scale to zero when not in use
autoscaling:
  minReplicas: 0
  maxReplicas: 5
  scaleDownDelaySeconds: 300  # 5 minutes idle before scale down
```

## Best Practices

### 1. Warm-Up Requests

```python
def warmup():
    """Send warm-up requests on startup."""
    sample_input = {"features": [0.0] * 10}
    for _ in range(5):
        predict(sample_input)
    print("Model warmed up")
```

### 2. Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.1)
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### 3. Async Processing

```python
import asyncio
import aiohttp

async def predict_async(session, data):
    async with session.post(url, json=data, headers=headers) as response:
        return await response.json()

async def batch_predict(items):
    async with aiohttp.ClientSession() as session:
        tasks = [predict_async(session, item) for item in items]
        return await asyncio.gather(*tasks)
```

### 4. Monitor and Iterate

1. Establish baseline metrics
2. Test under load
3. Identify bottlenecks
4. Optimize and repeat
