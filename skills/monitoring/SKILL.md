---
name: domino-monitoring
description: Monitor and analyze Domino platform usage — query run/job history, compute spend, execution status, cost allocation, and Gen-AI endpoint metrics. Access Grafana dashboards for fleet-level observability. Use when investigating job failures, analyzing compute costs, reviewing execution history, checking resource utilization trends, or accessing Grafana workload monitoring.
---

# Domino Monitoring & Observability Skill

## Description
This skill covers programmatic access to Domino's observability data: run history, job status, compute costs, Gen-AI endpoint telemetry, and the Grafana dashboards that show fleet-level execution health.

## Activation
Activate this skill when users want to:
- Query historical run/job/workspace execution data
- Analyze compute spend by user, project, or hardware tier
- Monitor active or recent job status and logs
- Access Grafana dashboards for workload or execution monitoring
- Pull Gen-AI endpoint request/latency/resource metrics
- Audit platform activity
- Build cost reports or usage dashboards

## Authentication
```bash
export DOMINO_API_KEY="$DOMINO_USER_API_KEY"   # set automatically inside Domino workspaces
export DOMINO_HOST="http://nucleus-frontend.domino-platform:80"  # internal; use your external hostname outside Domino
```
All REST calls use:
```
X-Domino-Api-Key: <your-api-key>
```

---

## 1. Run History — All Executions (Jobs, Workspaces, Apps, Launchers)

The most complete API for historical analysis. Returns all run types with duration and cost data.

**`GET /v4/gateway/runs/getByBatchId`**

> Requires admin-level API key for full deployment-wide data. Regular users get their own runs.

```bash
# First page (oldest runs first, from 2018)
curl -s "$DOMINO_HOST/v4/gateway/runs/getByBatchId" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY"

# Paginate using nextBatchId from previous response
curl -s "$DOMINO_HOST/v4/gateway/runs/getByBatchId?batchId=<nextBatchId>" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY"

# Get as CSV
curl -s "$DOMINO_HOST/v4/gateway/runs/getByBatchId" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -H "Accept: text/csv"
```

**Response fields:**
| Field | Description |
|---|---|
| `runId` | Unique execution ID |
| `title` | Run title |
| `command` | Script/command that was run |
| `status` | `Succeeded`, `Failed`, `Stopped`, `Error` |
| `runType` | `Batch`, `Workspace`, `App`, `Launcher`, `ModelDeploy` |
| `userName` / `userId` | Who ran it |
| `projectName` / `projectId` | Which project |
| `hardwareTier` | Hardware tier ID used |
| `runDurationSec` | Wall-clock seconds |
| `hardwareTierCostAmount` | Cost in `hardwareTierCostCurrency` |
| `totalCostAmount` | Total including cluster workers |
| `queuedTime` / `startTime` / `endTime` | Timing breakdown |
| `diskUsageGiB` / `diskUsagePercent` | Storage used |
| `computeClusterDetails` | Spark/Ray/Dask worker info (if applicable) |
| `nextBatchId` | Cursor for next page |

**Python — paginate all runs:**
```python
import os, requests

DOMINO_HOST = os.environ["DOMINO_HOST"]
HEADERS = {"X-Domino-Api-Key": os.environ["DOMINO_API_KEY"]}

def get_all_runs(max_pages=None):
    url = f"{DOMINO_HOST}/v4/gateway/runs/getByBatchId"
    batch_id = None
    all_runs = []
    pages = 0

    while True:
        params = {"batchId": batch_id} if batch_id else {}
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("runs", [])
        all_runs.extend(batch)
        pages += 1

        next_id = data.get("nextBatchId")
        if not next_id or not batch or (max_pages and pages >= max_pages):
            break
        batch_id = next_id

    return all_runs

# Example: summarize spend by hardware tier
from collections import defaultdict
runs = get_all_runs(max_pages=10)  # remove limit for full history

spend_by_tier = defaultdict(float)
count_by_tier = defaultdict(int)
for r in runs:
    tier = r.get("hardwareTier", "unknown")
    spend_by_tier[tier] += r.get("hardwareTierCostAmount", 0)
    count_by_tier[tier] += 1

for tier in sorted(spend_by_tier, key=spend_by_tier.get, reverse=True):
    print(f"{tier:30s}  runs={count_by_tier[tier]:5d}  cost=${spend_by_tier[tier]:.4f}")
```

---

## 2. Utilization Runs (Date-Filtered)

**`GET /v4/controlCenter/utilization/runs`**

> Requires SysAdmin role. Results cached with 30-minute TTL.

```bash
curl -s "$DOMINO_HOST/v4/controlCenter/utilization/runs" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -G \
  --data-urlencode "startDate=20260101" \
  --data-urlencode "endDate=20260402" \
  --data-urlencode "hardwareTierId=small-k8s"
  # optional: projectId=, startingUserId=, organizationId=
```

---

## 3. Jobs API (Project-Scoped)

For querying jobs within a specific project, including status, logs, and metadata.

### List Jobs
**`GET /api/jobs/beta/jobs?projectId={projectId}`**

```bash
curl -s "$DOMINO_HOST/api/jobs/beta/jobs?projectId=<projectId>&pageSize=20" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" | python3 -m json.tool
```

**Response fields per job:**
| Field | Description |
|---|---|
| `id` | Job ID |
| `number` | Sequential job number in project |
| `stageTimes.submissionTime` | When job was queued |
| `stageTimes.startTime` | When execution began |
| `stageTimes.completedTime` | When it finished |
| `runCommand` | Command executed |
| `title` | Human-readable label |
| `status.executionStatus` | `Succeeded`, `Failed`, `Running`, `Queued`, `Stopped` |
| `status.isCompleted` | Boolean |
| `status.isScheduled` | Whether it was a scheduled job |
| `dominoStats` | Custom stats logged by the run |
| `mainRepoGitRef` | Branch/commit used |

### Get Single Job
**`GET /api/jobs/beta/jobs/{jobId}`**

### Get Job Logs
**`GET /api/jobs/beta/jobs/{jobId}/logs`**

```python
import os, requests

DOMINO_HOST = os.environ["DOMINO_HOST"]
HEADERS = {"X-Domino-Api-Key": os.environ["DOMINO_API_KEY"]}

def get_recent_jobs(project_id, page_size=50):
    resp = requests.get(
        f"{DOMINO_HOST}/api/jobs/beta/jobs",
        headers=HEADERS,
        params={"projectId": project_id, "pageSize": page_size},
    )
    resp.raise_for_status()
    return resp.json()["jobs"]

def get_job_logs(job_id):
    resp = requests.get(f"{DOMINO_HOST}/api/jobs/beta/jobs/{job_id}/logs", headers=HEADERS)
    resp.raise_for_status()
    return resp.text

# Example: find all failed jobs in a project
jobs = get_recent_jobs("<your-project-id>")
failed = [j for j in jobs if j["status"]["executionStatus"] == "Failed"]
for j in failed:
    print(f"Job #{j['number']} — {j['title']} — {j['stageTimes'].get('completedTime')}")
```

### Python SDK Alternative
```python
from domino import Domino

d = Domino("owner/project-name")

# List recent runs
runs = d.runs_list()

# Job status
status = d.job_status(job_id)

# Start a job and wait
job = d.job_start_blocking(command="train.py", hardware_tier_name="small-k8s")
```

---

## 4. Cost & Spend APIs

> All cost endpoints require **SysAdmin** role.

### Check if Cost Feature is Active
```bash
curl -s "$DOMINO_HOST/api/cost/v1/costActivationStatus" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY"
```

### Cost Allocation Summary
```bash
# Last 7 days, grouped by project
curl -s "$DOMINO_HOST/api/cost/v2/allocation/summary" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -G \
  --data-urlencode "window=7d" \
  --data-urlencode "aggregate=projectName"

# Other window formats: "1d", "30d", "month", "lastmonth"
# Other aggregate values: "projectId", "invoiceEntityID"
```

### Full Allocation Detail
```bash
curl -s "$DOMINO_HOST/api/cost/v2/allocation" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -G --data-urlencode "window=7d"
```

### Accumulated Costs
```bash
curl -s "$DOMINO_HOST/api/cost/v2/allocation/accumulated" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -G --data-urlencode "window=30d"
```

### Cloud Billing Data
```bash
curl -s "$DOMINO_HOST/api/cost/v2/cloudCost/accumulated" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -G \
  --data-urlencode "window=7d" \
  --data-urlencode "aggregate=invoiceEntityID"
```

---

## 5. Gen-AI Endpoint Metrics (Beta)

For LLM/vLLM endpoints deployed via Domino's Gen-AI platform.

```bash
BASE="$DOMINO_HOST/api/gen-ai/beta/endpoints/{endpointId}/versions/{versionNumber}"

# Pod resource usage (CPU, memory)
curl -s "$BASE/pod-resource-metrics" -H "X-Domino-Api-Key: $DOMINO_API_KEY"

# HTTP request metrics (RPS, status codes)
curl -s "$BASE/request-metrics" -H "X-Domino-Api-Key: $DOMINO_API_KEY"

# vLLM latency percentiles
curl -s "$BASE/vllm-latency-metrics" -H "X-Domino-Api-Key: $DOMINO_API_KEY"

# vLLM token throughput
curl -s "$BASE/vllm-token-metrics" -H "X-Domino-Api-Key: $DOMINO_API_KEY"
```

---

## 6. Grafana Dashboards

Grafana is embedded in every Domino deployment at `https://<your-domino-domain>/grafana`.

**Access:** Browser only via Domino SSO — not reachable with just a Domino API key from inside a workspace pod. SysAdmins get Grafana Admin automatically.

**UI path:** Admin > Advanced > Grafana Monitoring

**To query programmatically:** A SysAdmin creates a Grafana service account token (Administration > Service Accounts > Add service account token), which can then be used from workspace pods since the external Domino URL is reachable from compute pods.

```bash
export GRAFANA_TOKEN="glsa_..."           # Grafana service account token
export DOMINO_EXTERNAL="https://<your-domino-domain>"
```

```python
import os, requests

GRAFANA_BASE = f"{os.environ['DOMINO_EXTERNAL']}/grafana/api"
GRAFANA_HEADERS = {"Authorization": f"Bearer {os.environ['GRAFANA_TOKEN']}"}

def grafana_get(path, **params):
    resp = requests.get(f"{GRAFANA_BASE}{path}", headers=GRAFANA_HEADERS, params=params or None)
    resp.raise_for_status()
    return resp.json()

def promql(query, start="now-1h", end="now", step="60s", datasource_id=1):
    """Range query via Grafana datasource proxy. datasource_id=1 is the default Prometheus."""
    resp = requests.get(
        f"{GRAFANA_BASE}/datasources/proxy/{datasource_id}/api/v1/query_range",
        headers=GRAFANA_HEADERS,
        params={"query": query, "start": start, "end": end, "step": step},
    )
    resp.raise_for_status()
    return resp.json()["data"]["result"]

def promql_instant(query, datasource_id=1):
    """Instant PromQL query (current value)."""
    resp = requests.get(
        f"{GRAFANA_BASE}/datasources/proxy/{datasource_id}/api/v1/query",
        headers=GRAFANA_HEADERS,
        params={"query": query},
    )
    resp.raise_for_status()
    return resp.json()["data"]["result"]
```

### Datasources

Domino Grafana deployments have two Prometheus datasources:
- **id 1** — `Prometheus` (default) — main platform metrics, Kubernetes, execution pods
- **id 2** — `CostAnalyzerPrometheus` — Kubecost cost allocation metrics

```python
# List datasources to confirm IDs on a given deployment
grafana_get("/datasources")
```

### Key Dashboards

The following dashboard UIDs are consistent across Domino deployments:

| UID | Dashboard | What It Shows |
|---|---|---|
| `domino-views-workloads` | Domino / Views / Workloads | Active executions by type/tier, pod phases, startup time by user |
| `domino_execution_overview` | Domino Execution Overview | Launch rate, success/failure counts, node pool scaling |
| `model-endpoint-monitoring` | Models Endpoint Monitoring | HTTP status codes, P50–P99 latency, RPS, CPU/memory/restarts |
| `domino_gpu_workspace_dataplanes` | GPU Utilization by Workspace | Per-workspace GPU utilization across data planes |
| `k8s_views_nodes3` | Kubernetes / Views / Nodes | Node-level CPU/memory/disk |
| `cluster_autoscaler_overview` | Kubernetes / System / Cluster Autoscaler | Scale-up/down events, pending pods |
| `k8s_views_pods` | Kubernetes / Views / Pods | Per-pod CPU/memory in any namespace |
| `karpenter` | Karpenter | Node provisioning events and pool state |
| `kubecost` | Kubecost - Billing Tags | Cost by billing tag |
| `genai-models` | GenAI Overview | LLM endpoint traffic and performance |
| `domino-admin-toolkit` | Domino Admin Toolkit | Admin-level platform health |

```python
# Inspect panels available in a dashboard
def list_dashboard_panels(uid):
    d = grafana_get(f"/dashboards/uid/{uid}")
    for panel in d["dashboard"].get("panels", []):
        print(f"  [{panel['id']:3d}] {panel.get('title', '(untitled)')}")

list_dashboard_panels("domino-views-workloads")
```

### Useful PromQL Queries

```python
# Active Domino execution pods by phase
promql_instant("count by (phase) (kube_pod_status_phase{namespace='domino-compute'})")

# CPU usage per execution pod (top 20)
promql_instant(
    "topk(20, sum by (pod) (rate(container_cpu_usage_seconds_total"
    "{namespace='domino-compute', container!=''}[5m])) * 100)"
)

# Memory usage per execution pod (GiB, top 20)
promql_instant(
    "topk(20, sum by (pod) (container_memory_working_set_bytes"
    "{namespace='domino-compute', container!=''})) / 1e9"
)

# GPU utilization per pod
promql_instant("sum by (pod) (DCGM_FI_DEV_GPU_UTIL{namespace='domino-compute'})")

# CPU over time for a specific run (pod name matches run ID prefix)
run_id = "<jobId>"
promql(
    f"rate(container_cpu_usage_seconds_total{{namespace='domino-compute',"
    f"pod=~'run-{run_id}.*', container!=''}}[5m]) * 100",
    start="now-4h", end="now", step="60s"
)

# Node pool utilization (allocatable vs requested, domino-compute only)
promql_instant(
    "(sum by (node) (kube_pod_container_resource_requests{resource='cpu', namespace='domino-compute'}))"
    " / sum by (node) (kube_node_status_allocatable{resource='cpu'})"
)

# Pending pods (waiting for a node)
promql_instant("count(kube_pod_status_phase{namespace='domino-compute', phase='Pending'})")
```

---

## 7. Audit Trail

```bash
# Platform-wide audit events
curl -s "$DOMINO_HOST/auditevents" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" | python3 -m json.tool

# AI Gateway audit
curl -s "$DOMINO_HOST/api/aigateway/v1/audit" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" | python3 -m json.tool

# Data source audit
curl -s "$DOMINO_HOST/api/datasource/v1/audit" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" | python3 -m json.tool
```

---

## Common Analysis Recipes

### Cost by User (Last 30 Days)
```python
from collections import defaultdict
from datetime import datetime, timezone, timedelta

runs = get_all_runs(max_pages=50)
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
spend = defaultdict(float)

for r in runs:
    end = r.get("endTime")
    if not end:
        continue
    if datetime.fromisoformat(end.replace("Z", "+00:00")) < cutoff:
        continue
    spend[r["userName"]] += r.get("hardwareTierCostAmount", 0)

for user, cost in sorted(spend.items(), key=lambda x: x[1], reverse=True):
    print(f"{user:30s}  ${cost:.4f}")
```

### Job Failure Rate by Project
```python
from collections import Counter, defaultdict

runs = get_all_runs(max_pages=20)
by_project = defaultdict(Counter)
for r in [r for r in runs if r["runType"] == "Batch"]:
    by_project[r["projectName"]][r["status"]] += 1

for project, counts in sorted(by_project.items()):
    total = sum(counts.values())
    failed = counts.get("Failed", 0) + counts.get("Error", 0)
    print(f"{project:40s}  total={total:4d}  failed={failed:3d}  ({100*failed/total:.0f}%)")
```

### Average Queue Time by Hardware Tier
```python
from datetime import datetime
from collections import defaultdict

def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None

runs = get_all_runs(max_pages=20)
queue_times = defaultdict(list)

for r in runs:
    q, s = parse_dt(r.get("queuedTime")), parse_dt(r.get("startTime"))
    if q and s:
        queue_times[r["hardwareTier"]].append((s - q).total_seconds())

for tier, times in sorted(queue_times.items()):
    avg = sum(times) / len(times)
    print(f"{tier:30s}  avg_queue={avg:.1f}s  samples={len(times)}")
```

---

## Limitations

| Limitation | Details |
|---|---|
| Per-run CPU/memory time series | Not in the Domino REST API. Query via Grafana/Prometheus using `pod=~'run-<runId>.*'` against the `domino-compute` namespace. Requires a Grafana service account token. |
| `/v4/gateway/runs/getByBatchId` paging direction | Pages oldest-first; to get recent runs paginate to the end, or use the jobs API with a known `projectId` |
| Cost APIs | Require SysAdmin role; return empty for non-admin users |
| Utilization API cache | 30-minute TTL — recent data may be stale |
| `jobs/beta` endpoints | Beta — query parameters beyond `projectId` are undocumented; inspect `/api/jobs/beta/openapi` on your instance |

---

## Documentation Reference
- [Export Compute and Spend Data](https://docs.dominodatalab.com/en/latest/admin_guide/9a12a0/export-compute-and-spend-data-with-the-api/)
- [Analyze Costs](https://docs.dominodatalab.com/en/latest/admin_guide/157618/analyze-costs/)
- [Use Grafana Dashboards](https://docs.dominodatalab.com/en/latest/admin_guide/169f0f/use-grafana-dashboards/)
- [Standard Grafana Dashboards](https://docs.dominodatalab.com/en/latest/admin_guide/57dff6/standard-dashboards/)
- [Execution Monitoring Dashboards](https://docs.dominodatalab.com/en/cloud/admin_guide/704998/use-execution-monitoring-dashboards/)
- [Model Endpoint Monitoring](https://docs.dominodatalab.com/en/cloud/admin_guide/07a82b/use-model-endpoint-monitoring-dashboards/)
- [Monitoring and Alerting](https://docs.dominodatalab.com/en/latest/admin_guide/d30657/monitoring-and-alerting/)
- [Audit Trail API](https://docs.dominodatalab.com/en/latest/admin_guide/a157c4/using-the-audit-trail-api/)
