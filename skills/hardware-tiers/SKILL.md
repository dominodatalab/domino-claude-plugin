---
name: domino-hardware-tiers
description: Manage Domino Hardware Tiers - create, update, list, and archive compute resource configurations (CPU, memory, GPU). Covers tier flags, node pools, GPU setup, over-provisioning, pod customization, and cost settings. Use when creating or editing hardware tiers, configuring default tiers, setting GPU resources, or troubleshooting hardware tier availability.
---

# Domino Hardware Tiers Skill

## Description
This skill helps administrators manage Domino Hardware Tiers — the named compute resource configurations (CPU cores, memory, GPU) that users select when launching workspaces, jobs, and model endpoints.

## Activation
Activate this skill when users want to:
- List available hardware tiers
- Create a new hardware tier
- Update an existing hardware tier's resources, flags, or settings
- Archive (deactivate) a hardware tier
- Configure GPU hardware tiers
- Set a default hardware tier
- Configure tier visibility, global availability, or cost
- Troubleshoot hardware tier capacity or availability issues

## Required Permissions
- **`ViewHardwareTiers`** — for read operations (list, get)
- **`ManageHardwareTiers`** — for write operations (create, update, archive)

## Authentication
All API calls require an API key header:
```
X-Domino-Api-Key: <your-api-key>
```
Obtain your key from: **Account > Account Settings > API Key**

Set it as an environment variable for convenience:
```bash
export DOMINO_API_KEY="your-api-key"
export DOMINO_HOST="https://your-domino-instance.com"
```

---

## API Reference

Base path: `$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers`

### List All Hardware Tiers
```bash
curl -X GET "$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -G \
  --data-urlencode "offset=0" \
  --data-urlencode "limit=50" \
  --data-urlencode "includeArchived=false"
```

**Query parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `offset` | integer | 0 | Number of tiers to skip (pagination) |
| `limit` | integer | 10 | Number of tiers to return |
| `includeArchived` | boolean | false | Include archived/deactivated tiers |

### Get a Hardware Tier by ID
```bash
curl -X GET "$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY"
```

### Create a Hardware Tier
```bash
curl -X POST "$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "small-k8s",
    "name": "Small",
    "nodePool": "default",
    "resources": {
      "cores": 1.0,
      "coresLimit": 2.0,
      "memory": { "value": 4.0, "units": "GiB" },
      "memoryLimit": { "value": 8.0, "units": "GiB" },
      "allowSharedMemoryToExceedDefault": false
    },
    "centsPerMinute": 0.0,
    "flags": {
      "isDefault": false,
      "isVisible": true,
      "isGlobal": true,
      "isDataAnalystTier": false
    }
  }'
```

### Update a Hardware Tier
The PUT endpoint takes the full `HardwareTierV1` object (as returned by GET). The recommended workflow is:
1. GET the existing tier
2. Modify the desired fields
3. PUT the full object back

```bash
# Step 1: Fetch existing tier
TIER=$(curl -s -X GET "$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY")

# Step 2: Modify and PUT (example: update memory to 16 GiB using jq)
echo $TIER | jq '.hardwareTier.resources.memory.value = 16' | jq '.hardwareTier' | \
curl -X PUT "$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY" \
  -H "Content-Type: application/json" \
  -d @-
```

### Archive (Deactivate) a Hardware Tier
Archive hides the tier from users without permanently deleting it. Archived tiers can be retrieved with `includeArchived=true`.
```bash
curl -X DELETE "$DOMINO_HOST/api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}" \
  -H "X-Domino-Api-Key: $DOMINO_API_KEY"
```

---

## Python Examples

```python
import os
import requests

DOMINO_HOST = os.environ["DOMINO_HOST"]
DOMINO_API_KEY = os.environ["DOMINO_API_KEY"]
BASE_URL = f"{DOMINO_HOST}/api/hardwaretiers/v1/hardwaretiers"
HEADERS = {"X-Domino-Api-Key": DOMINO_API_KEY, "Content-Type": "application/json"}


def list_hardware_tiers(include_archived=False):
    resp = requests.get(
        BASE_URL,
        headers=HEADERS,
        params={"limit": 100, "includeArchived": include_archived},
    )
    resp.raise_for_status()
    return resp.json()["hardwareTiers"]


def get_hardware_tier(tier_id):
    resp = requests.get(f"{BASE_URL}/{tier_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["hardwareTier"]


def create_hardware_tier(tier: dict):
    resp = requests.post(BASE_URL, headers=HEADERS, json=tier)
    resp.raise_for_status()
    return resp.json()["hardwareTier"]


def update_hardware_tier(tier: dict):
    """tier must be the full HardwareTierV1 object (from a GET response)."""
    resp = requests.put(BASE_URL, headers=HEADERS, json=tier)
    resp.raise_for_status()
    return resp.json()["hardwareTier"]


def archive_hardware_tier(tier_id: str):
    resp = requests.delete(f"{BASE_URL}/{tier_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["hardwareTier"]


# Example: Create a small CPU tier
new_tier = create_hardware_tier({
    "id": "small-k8s",
    "name": "Small",
    "nodePool": "default",
    "resources": {
        "cores": 1.0,
        "coresLimit": 2.0,
        "memory": {"value": 4.0, "units": "GiB"},
        "memoryLimit": {"value": 8.0, "units": "GiB"},
        "allowSharedMemoryToExceedDefault": False,
    },
    "centsPerMinute": 0.0,
    "flags": {
        "isDefault": False,
        "isVisible": True,
        "isGlobal": True,
        "isDataAnalystTier": False,
    },
})

# Example: Update memory on an existing tier
tier = get_hardware_tier("small-k8s")
tier["resources"]["memory"] = {"value": 16.0, "units": "GiB"}
updated = update_hardware_tier(tier)
```

---

## Schema Reference

### `HardwareTierResourcesV1`
| Field | Required | Description |
|---|---|---|
| `cores` | Yes | CPU cores request (float) |
| `memory` | Yes | Memory request — `{"value": float, "units": "GiB"\|"MiB"\|"GB"\|"MB"}` |
| `allowSharedMemoryToExceedDefault` | Yes | Allow `/dev/shm` to exceed default |
| `coresLimit` | No | CPU cores limit (burstable) |
| `memoryLimit` | No | Memory limit |
| `memorySwapLimit` | No | Memory + swap limit |
| `sharedMemoryLimit` | No | `/dev/shm` size limit |

### `HardwareTierFlagsV1`
| Flag | Description |
|---|---|
| `isDefault` | Used as the default tier for new workspaces/jobs |
| `isVisible` | Visible to end users in the UI |
| `isGlobal` | Available across all projects |
| `isArchived` | Tier is deactivated (read-only, set via DELETE endpoint) |
| `isDataAnalystTier` | Restricted to Data Analyst role |
| `isModelApiTier` | Available for Model API deployments |
| `isDefaultForModelApi` | Default tier for Model API deployments |

### `HardwareTierGpuConfigurationV1`
| Field | Required | Example |
|---|---|---|
| `numberOfGpus` | Yes | `1` |
| `gpuKey` | Yes | `"nvidia.com/gpu"`, `"nvidia.com/mig-1g.5gb"` |

### `HardwareTierComputeClusterRestrictionsV1`
Restrict tier to specific cluster types only:
```json
{
  "restrictToSpark": false,
  "restrictToRay": false,
  "restrictToDask": false,
  "restrictToMpi": false
}
```

### `HardwareTierOverProvisioningV1`
Pre-warm instances on a schedule to reduce cold-start latency:
```json
{
  "instances": 2,
  "schedulingEnabled": true,
  "daysOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  "timezone": "America/New_York",
  "fromTime": "08:00",
  "toTime": "18:00"
}
```

### `HardwareTierPodCustomizationV1`
Advanced Kubernetes pod settings:
```json
{
  "additionalAnnotations": {},
  "additionalLabels": {},
  "additionalLimits": {},
  "additionalRequests": {},
  "capabilities": ["IPC_LOCK"],
  "hugepages": {"2Mi": "100Mi"}
}
```

---

## Common Recipes

### Create a GPU Tier
```python
gpu_tier = create_hardware_tier({
    "id": "gpu-t4",
    "name": "GPU - T4",
    "nodePool": "gpu-t4-pool",
    "resources": {
        "cores": 4.0,
        "memory": {"value": 16.0, "units": "GiB"},
        "allowSharedMemoryToExceedDefault": False,
    },
    "gpuConfiguration": {
        "numberOfGpus": 1,
        "gpuKey": "nvidia.com/gpu",
    },
    "centsPerMinute": 0.0,
    "flags": {
        "isDefault": False,
        "isVisible": True,
        "isGlobal": True,
        "isDataAnalystTier": False,
    },
})
```

### Set a Tier as the Default
```python
tier = get_hardware_tier("small-k8s")
tier["flags"]["isDefault"] = True
update_hardware_tier(tier)
```

### Hide a Tier Without Archiving
```python
tier = get_hardware_tier("large-k8s")
tier["flags"]["isVisible"] = False
update_hardware_tier(tier)
```

### Make a Tier Available Only for Model APIs
```python
tier = get_hardware_tier("inference-tier")
tier["flags"]["isModelApiTier"] = True
tier["flags"]["isDefaultForModelApi"] = True
update_hardware_tier(tier)
```

---

## Capacity Fields (Read-Only)
The `capacity` field is returned in GET responses and shows live utilization:
- `numberOfExecutors` — currently running executions
- `maxNumberOfExecutors` — maximum allowed concurrent executions
- `capacityLevel` — `"CanExecuteWithCurrentInstances"` | `"RequiresLaunchingInstance"` | `"Full"` | `"Unknown"`

Do not include `capacity` in POST/PUT request bodies.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| 403 Forbidden | Your API key's user lacks `ManageHardwareTiers` permission. Request admin access. |
| Tier not visible to users | Check `flags.isVisible = true` and `flags.isGlobal = true` (or tier is project-scoped) |
| GPU tier not scheduling | Verify `nodePool` matches the actual Kubernetes node pool label for GPU nodes |
| `400 Bad Request` on PUT | PUT requires the full `HardwareTierV1` object including `creationTime`, `updateTime`, `flags`, and `podCustomization`; always GET first, then modify |
| Tier shows as "Full" | Increase `maxSimultaneousExecutions` or provision more nodes in the node pool |

## Documentation Reference
- [Domino Platform API Reference](https://docs.dominodatalab.com/en/cloud/api_guide/8c929e/domino-platform-api-reference/)
- [Hardware Tiers Overview](https://docs.dominodatalab.com/en/latest/admin_guide/hardware_tiers/)
