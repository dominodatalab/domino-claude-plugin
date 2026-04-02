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
import os, requests, time

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

## 6. New Relic (Infrastructure & APM Metrics)

This Domino deployment uses New Relic for cluster-level observability. The New Relic agents inject metadata into every execution pod (`NEW_RELIC_METADATA_KUBERNETES_*` env vars), so all pod metrics are tagged with Domino project, namespace, node, and cluster.

**Confirmed account details (from this deployment):**
- Account ID: `4131420`
- Cluster: `cloud-dogfood`
- Namespace: `domino-compute`

### Querying New Relic via NerdGraph (GraphQL)

The NerdGraph API at `https://api.newrelic.com/graphql` is reachable from Domino workspace pods. It requires a **New Relic User API key** — get one from [one.newrelic.com](https://one.newrelic.com) under Account > API Keys > User key.

> The browser license key (`NRJS-...`) visible in the Domino UI source is **write-only** and cannot be used to query data.

```bash
export NR_API_KEY="NRAK-..."  # your User API key
export NR_ACCOUNT_ID="4131420"

# Run a NRQL query via NerdGraph
curl -s -X POST "https://api.newrelic.com/graphql" \
  -H "Content-Type: application/json" \
  -H "API-Key: $NR_API_KEY" \
  -d "{
    \"query\": \"{ actor { account(id: $NR_ACCOUNT_ID) { nrql(query: \\\"SELECT average(cpuPercent) FROM SystemSample FACET podName SINCE 1 hour ago\\\") { results } } } }\"
  }" | python3 -m json.tool
```

### Python Helper

```python
import os, requests

NR_API_KEY = os.environ["NR_API_KEY"]   # New Relic User API key
NR_ACCOUNT_ID = 4131420

def nrql_query(nrql: str) -> list:
    """Run a NRQL query and return the results list."""
    query = """
    {
      actor {
        account(id: %d) {
          nrql(query: "%s") {
            results
          }
        }
      }
    }
    """ % (NR_ACCOUNT_ID, nrql.replace('"', '\\"'))

    resp = requests.post(
        "https://api.newrelic.com/graphql",
        headers={"Content-Type": "application/json", "API-Key": NR_API_KEY},
        json={"query": query},
    )
    resp.raise_for_status()
    return resp.json()["data"]["actor"]["account"]["nrql"]["results"]
```

### Useful NRQL Queries for Domino Workloads

```python
# CPU usage by pod in domino-compute namespace (last hour)
results = nrql_query(
    "SELECT average(cpuPercent) FROM SystemSample "
    "WHERE namespaceName = 'domino-compute' "
    "FACET podName SINCE 1 hour ago LIMIT 50"
)

# Memory usage by pod
results = nrql_query(
    "SELECT average(memoryUsedBytes) / 1e9 AS 'memory_GiB' FROM SystemSample "
    "WHERE namespaceName = 'domino-compute' "
    "FACET podName SINCE 1 hour ago LIMIT 50"
)

# Pod CPU over time (time series)
results = nrql_query(
    "SELECT average(cpuPercent) FROM SystemSample "
    "WHERE podName = 'run-<jobId>-xxxxx' "
    "TIMESERIES 1 minute SINCE 2 hours ago"
)

# Node-level resource utilization
results = nrql_query(
    "SELECT average(cpuPercent), average(memoryUsedPercent) FROM SystemSample "
    "WHERE clusterName = 'cloud-dogfood' "
    "FACET nodeName SINCE 1 hour ago"
)

# GPU utilization (if NR GPU agent is installed)
results = nrql_query(
    "SELECT average(gpu.utilization) FROM NvidiaSmiSample "
    "FACET podName SINCE 1 hour ago"
)

# Container restart count (stability signal)
results = nrql_query(
    "SELECT sum(restartCount) FROM K8sContainerSample "
    "WHERE namespaceName = 'domino-compute' "
    "FACET containerName, podName SINCE 24 hours ago"
)
```

### Finding the Pod Name for a Specific Run

New Relic metrics are tagged by pod name. Domino pod names follow the pattern `run-<runId>-<suffix>`. Match your run ID from the runs API to the pod name:

```python
run_id = "69ce9a6589f63840b4992c0d"  # from /v4/gateway/runs or /api/jobs/beta/jobs

results = nrql_query(
    f"SELECT average(cpuPercent), average(memoryUsedPercent) FROM SystemSample "
    f"WHERE podName LIKE 'run-{run_id}%' "
    f"TIMESERIES 1 minute SINCE 4 hours ago"
)
```

---

## 7. Grafana Dashboards

Grafana is embedded in Domino at `https://<your-domino-domain>/grafana` and `/grafana-workload`.

**Access:** Browser only — requires Domino SSO session. SysAdmins get Grafana Admin automatically. The path returns 403 when accessed without a valid browser session; it cannot be reached with just a Domino API key from inside a workspace pod.

**UI path:** Admin > Advanced > Grafana Monitoring

**To query programmatically:** Generate a Grafana service account token in the Grafana UI (Administration > Service Accounts), then use the Grafana HTTP API:

```python
import os, requests

# External Domino URL (not the internal nucleus-frontend hostname)
DOMINO_EXTERNAL = "https://<your-domino-domain>"
GRAFANA_BASE = f"{DOMINO_EXTERNAL}/grafana/api"
GRAFANA_HEADERS = {"Authorization": "Bearer <grafana-service-account-token>"}

# List dashboards
resp = requests.get(f"{GRAFANA_BASE}/search?type=dash-db", headers=GRAFANA_HEADERS)
dashboards = resp.json()

# Query Prometheus via Grafana datasource proxy
resp = requests.get(
    f"{GRAFANA_BASE}/datasources/proxy/1/api/v1/query_range",
    headers=GRAFANA_HEADERS,
    params={
        "query": "count by (phase) (kube_pod_status_phase{namespace='domino-compute'})",
        "start": "1h",
        "end": "now",
        "step": "60",
    }
)
```

### Key Dashboards

| Dashboard | What It Shows |
|---|---|
| **Domino / Views / Workloads** | Active executions by type/tier, pod phases, startup time by user |
| **Domino Execution Overview** | Launch rate, success rate, failure reasons, node pool scaling |
| **Execution Monitoring** | Time to Available, startup phase breakdown (NodeAssigned → ImagesPulled → VolumesMounted → FilesPrepared → Running) |
| **Model Endpoint Monitoring** | HTTP status codes, P50/P90/P95/P99 latency, RPS, CPU/memory/restarts |
| **Kubernetes / Nodes** | Node-level CPU/memory/disk across cluster |
| **Cluster Autoscaler** | Scale-up/down events, pending pods, node pool sizes |

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
runs = get_all_runs(max_pages=50)  # adjust for your data volume

from collections import defaultdict
from datetime import datetime, timezone, timedelta

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
from collections import Counter

runs = get_all_runs(max_pages=20)
batch_runs = [r for r in runs if r["runType"] == "Batch"]

outcomes = Counter()
by_project = defaultdict(Counter)
for r in batch_runs:
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
| Per-run CPU/memory time series | Not in the Domino REST API. Available via New Relic NerdGraph (NRQL on `SystemSample`) using the pod name from the run ID. Requires a New Relic User API key. |
| `/v4/gateway/runs/getByBatchId` paging direction | Pages oldest-first; to get recent runs you must paginate to the end or use the jobs API with a known `projectId` |
| Cost APIs | Require SysAdmin role; return empty for non-admin users |
| Utilization API cache | 30-minute TTL — recent data may be stale |
| `jobs/beta` endpoints | Beta — query parameters beyond `projectId` are undocumented; test against `/api/jobs/beta/openapi` on your instance |

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
