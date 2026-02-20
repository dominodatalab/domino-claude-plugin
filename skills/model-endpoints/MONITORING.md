# Monitoring Model Endpoints

This guide covers monitoring model API endpoints using Domino's built-in Grafana dashboards and alerting.

## Key Metrics to Monitor

| Metric | Description | Target |
|--------|-------------|--------|
| CPU Usage | Processor utilization | < 80% sustained |
| Memory Usage | RAM utilization | Stable, no growth |
| Latency P50 | Median response time | < 100ms |
| Latency P95 | 95th percentile | < 300ms |
| Latency P99 | 99th percentile | < 500ms |
| Error Rate | Percentage of 4xx/5xx | < 1% |
| Request Rate | Requests per second | Varies by use case |
| Status Codes | Distribution of responses | Mostly 2xx |

## Accessing Grafana Dashboards

### Via Domino UI

1. Navigate to your project
2. Go to **Publish** → **Model APIs**
3. Select your model
4. Click **Monitoring** tab
5. Opens Grafana dashboard

### Grafana Dashboard Features

- **Real-time metrics**: Updates every few seconds
- **Time range selection**: Last 1h, 24h, 7d, etc.
- **Multiple panels**: CPU, memory, latency, errors
- **Drill-down**: Click panels for details

## CPU and Memory Monitoring

### What to Look For

**CPU Usage:**
- Consistent patterns indicate normal operation
- Spikes correlate with request bursts
- Sustained high usage may need scaling

**Memory Usage:**
- Should stabilize after model initialization
- Continuous growth indicates memory leak
- Sudden drops may indicate restarts

### Grafana CPU Query

```promql
# CPU usage percentage
100 * (1 - avg(rate(container_cpu_usage_seconds_total{
  pod=~"model-.*"
}[5m])))
```

### Grafana Memory Query

```promql
# Memory usage in MB
container_memory_usage_bytes{pod=~"model-.*"} / 1024 / 1024
```

## Latency Monitoring

### Understanding Latency Percentiles

| Percentile | Meaning |
|------------|---------|
| P50 (median) | Half of requests faster than this |
| P95 | 95% of requests faster than this |
| P99 | 99% of requests faster than this |

### Latency Distribution Query

```promql
# P50 latency
histogram_quantile(0.50, sum(rate(nginx_ingress_controller_request_duration_seconds_bucket{
  path=~"/models/MODEL_ID.*"
}[5m])) by (le))

# P95 latency
histogram_quantile(0.95, sum(rate(nginx_ingress_controller_request_duration_seconds_bucket{
  path=~"/models/MODEL_ID.*"
}[5m])) by (le))

# P99 latency
histogram_quantile(0.99, sum(rate(nginx_ingress_controller_request_duration_seconds_bucket{
  path=~"/models/MODEL_ID.*"
}[5m])) by (le))
```

### Latency Analysis Tips

1. **Baseline**: Establish normal latency range
2. **Correlate**: Check if spikes match deployments or traffic changes
3. **Investigate**: High P99 with low P50 suggests occasional slow requests

## Error Rate Monitoring

### Status Code Analysis

```promql
# Error rate percentage
100 * (
  sum(increase(nginx_ingress_controller_requests{
    status=~"400|402|403|404|405|406|408|429|5..",
    path=~"/models/MODEL_ID.*"
  }[$__range]))
  /
  sum(increase(nginx_ingress_controller_requests{
    path=~"/models/MODEL_ID.*"
  }[$__range]))
)
```

### Status Code Breakdown

```promql
# Requests by status code
sum(increase(nginx_ingress_controller_requests{
  path=~"/models/MODEL_ID.*"
}[$__range])) by (status)
```

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Check client input format |
| 401 | Unauthorized | Verify API token |
| 404 | Not Found | Check model ID/version |
| 429 | Too Many Requests | Rate limiting hit |
| 500 | Internal Error | Check model logs |
| 502 | Bad Gateway | Model pod issues |
| 503 | Service Unavailable | Model not ready |
| 504 | Gateway Timeout | Model too slow |

## Request Traffic Analysis

### Traffic Volume Query

```promql
# Requests per minute
sum(rate(nginx_ingress_controller_requests{
  path=~"/models/MODEL_ID.*"
}[1m])) * 60
```

### Traffic Patterns

- **Daily patterns**: Business hours vs. off-hours
- **Weekly patterns**: Weekday vs. weekend
- **Anomalies**: Unexpected spikes or drops

## Creating Alerts

### Alert Types

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | > 5% for 5 min | Critical |
| High Latency | P99 > 2s for 5 min | Warning |
| High CPU | > 90% for 10 min | Warning |
| Memory Leak | Growth > 10%/hour | Critical |
| Low Traffic | < 1 req/min for 15 min | Info |

### Grafana Alert Configuration

1. Open dashboard panel
2. Click **Edit** → **Alert** tab
3. Configure conditions:
   - **Query**: Metric to monitor
   - **Condition**: Threshold and duration
   - **Notifications**: Where to send alerts

### Example Alert Rules

**High Error Rate Alert:**
```yaml
name: High Error Rate
condition: error_rate > 5
for: 5m
labels:
  severity: critical
annotations:
  summary: "Model endpoint error rate above 5%"
  description: "Error rate is {{ $value }}%"
```

**High Latency Alert:**
```yaml
name: High Latency
condition: latency_p99 > 2
for: 5m
labels:
  severity: warning
annotations:
  summary: "Model P99 latency above 2 seconds"
  description: "P99 latency is {{ $value }}s"
```

## Building Custom Dashboards

### Dashboard JSON Structure

```json
{
  "title": "Model Endpoint Monitoring",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(rate(nginx_ingress_controller_requests{path=~\"/models/MODEL_ID.*\"}[1m])) * 60"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "stat",
      "targets": [
        {
          "expr": "100 * sum(rate(nginx_ingress_controller_requests{status=~\"5..\",path=~\"/models/MODEL_ID.*\"}[5m])) / sum(rate(nginx_ingress_controller_requests{path=~\"/models/MODEL_ID.*\"}[5m]))"
        }
      ]
    }
  ]
}
```

### Useful Panel Types

| Type | Use Case |
|------|----------|
| Graph | Time series (latency, traffic) |
| Stat | Single value (current error rate) |
| Gauge | Current value with thresholds |
| Table | Breakdown by dimension |
| Heatmap | Latency distribution |

## Debugging Issues

### High Latency Investigation

1. Check CPU usage during slow requests
2. Review model logs for errors
3. Test model locally for comparison
4. Check input data size
5. Review recent code changes

### Memory Leak Investigation

```python
# Add to model.py for debugging
import tracemalloc

tracemalloc.start()

def predict(data):
    result = model.predict(data)

    # Log memory usage periodically
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")

    return result
```

### Error Investigation

1. Check Grafana for error spike timing
2. Review model pod logs
3. Check for correlations with traffic or deployments
4. Test endpoint with sample requests
5. Review error response bodies

## Log Analysis

### Accessing Model Logs

1. Go to Model API in Domino UI
2. Click **Logs** tab
3. View stdout/stderr from model

### Log Patterns to Watch

```
# Startup issues
ERROR: Model failed to load

# Memory issues
MemoryError: Unable to allocate

# Timeout issues
Request timeout after 30 seconds

# Input issues
ValueError: Invalid input shape
```

## Best Practices

### 1. Set Up Baseline Monitoring

- Record metrics for 1 week before alerting
- Understand normal patterns
- Set thresholds based on baseline

### 2. Use SLOs

Define Service Level Objectives:
- Availability: 99.9%
- Latency P99: < 500ms
- Error rate: < 0.1%

### 3. Monitor Business Metrics

Beyond technical metrics:
- Predictions per customer
- Model usage by feature
- Accuracy (if labels available)

### 4. Regular Review

- Weekly: Review dashboards
- Monthly: Analyze trends
- Quarterly: Update thresholds
