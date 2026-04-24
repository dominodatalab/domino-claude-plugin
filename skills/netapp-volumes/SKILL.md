---
name: netapp-volumes
description: Work with Domino Volumes for NetApp ONTAP - enterprise-grade, multi-terabyte storage with near-instant snapshots. Covers volume creation, snapshot versioning with commit messages, cross-project sharing, mount paths (/mnt/netapp-volumes/ or /domino/netapp-volumes/), and the NetApp Volumes REST API. Use when managing large-scale data storage, needing fast no-copy snapshots, or integrating existing NetApp ONTAP infrastructure with Domino.
---

# Domino NetApp Volumes Skill

## Description
This skill helps users work with Domino Volumes for NetApp ONTAP — enterprise-grade storage that mounts NetApp ONTAP filesystems directly into Domino workloads, enabling multi-terabyte scale with near-instant snapshotting.

## Activation
Activate this skill when users want to:
- Create or manage NetApp Volumes in Domino
- Work with NetApp volume snapshots and versioning
- Share large-scale data across projects or teams
- Access existing NetApp ONTAP storage from Domino workspaces, jobs, or apps
- Use the NetApp Volumes REST API programmatically
- Understand mount paths for NetApp volumes
- Choose between NetApp Volumes and Domino Datasets

## What is a Domino NetApp Volume?

A Domino NetApp Volume is:
- **Enterprise-grade storage**: Backed by NetApp ONTAP via Kubernetes PVCs with the `netapp-storage` storage class
- **Multi-terabyte scale**: No practical upper limit — suitable for very large datasets
- **Near-instant snapshots**: ~3 seconds even for 100+ GB volumes using redirect-on-write (no extra storage consumed at snapshot time)
- **Versioned with commit messages**: Snapshots support human-readable tags and commit messages, unlike Datasets
- **Shareable**: Attach a single volume to multiple projects and teams
- **Persistent**: Data persists across executions

### NetApp Volumes vs. Domino Datasets

| Feature | NetApp Volumes | Domino Datasets |
|---------|---------------|-----------------|
| Storage backend | External NetApp ONTAP | Domino-managed NFS/EFS |
| Data scale | Multi-terabyte and beyond | Up to ~1 TB |
| Snapshot speed | ~3 seconds (any size) | Scales with data size |
| Snapshot storage cost | No extra space (redirect-on-write) | Duplicates physical data |
| Commit messages on snapshots | Supported | Not supported |
| Create new volume from snapshot | Read-only clones | Can create editable dataset |
| Cross-project sharing | Yes | Yes |
| Admin prerequisite | Admin must register filesystems | None |
| REST API | Full dedicated API | Via Domino Python SDK |

**Use NetApp Volumes when:**
- Data exceeds ~1 TB
- Near-instant snapshotting is required
- Your organization already has NetApp ONTAP infrastructure
- You need snapshot commit messages for audit trails
- High-performance shared storage across many teams

**Use Domino Datasets when:**
- Data is Domino-managed with no external infrastructure dependency
- You need to create editable new versions from snapshots
- Data is under ~1 TB

---

## Prerequisites

An admin must register at least one NetApp filesystem (Kubernetes PVC with the `netapp-storage` label) before users can create volumes. Contact your Domino administrator if no filesystems are available.

---

## Creating a NetApp Volume

### From the Domino Home Page
1. Navigate to **Data > NetApp Volumes** in the toolbar
2. Click **Add NetApp Volume > Create Volume**
3. Fill in the form:
   - **Name**: Letters, numbers, underscores, hyphens only
   - **Description**: Brief overview of the data
   - **Data Plane**: Select from available options
   - **NetApp Filesystem**: Choose a registered filesystem
   - **Capacity**: Set maximum storage allocation
4. Click **Next** to configure permissions
5. Assign users with **Reader / Editor / Owner** roles
6. Click **Finish**
7. Manually add the volume to projects afterward

### From within a Project (recommended — auto-associates)
1. Open a project → **Data > NetApp Volumes** (left panel)
2. Click **Add NetApp Volume > Create Volume**
3. Fill in the same form fields as above
4. The volume is automatically associated with the current project on creation

### Via REST API
```python
import os
import requests

# Auth token from in-cluster token service
token = requests.get("http://localhost:8899/access-token").text.strip()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

api_url = os.environ["DOMINO_API_HOST"]
remotefs_url = os.environ["DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT"]

# Look up your user ID (username is available in the DOMINO_USER_NAME env var)
user_resp = requests.get(
    f"{api_url}/v4/users?userName={os.environ['DOMINO_USER_NAME']}",
    headers=headers
).json()
user_id = user_resp[0]["id"]

# Create a volume (capacity is in bytes; grants is required)
response = requests.post(
    f"{remotefs_url}/remotefs/v1/volumes",
    headers=headers,
    json={
        "name": "large-training-data",
        "description": "Multi-TB training dataset for vision models",
        "filesystemId": "<filesystem-id>",
        "capacity": 5_000_000_000_000,  # 5 TB in bytes
        "grants": [
            {"targetId": user_id, "targetRole": "VolumeOwner"}
        ]
    }
)
volume = response.json()
print(f"Created volume ID: {volume['id']}")
```

---

## Adding a Volume to a Project

### Via Domino UI
1. Go to project → **Data > NetApp Volumes**
2. Click **Add NetApp Volume > Add Existing Volume**
3. Select the volume from the list
4. Configure access level for the project

### Via REST API
```python
# Attach a volume to a project
requests.post(
    f"{remotefs_url}/remotefs/v1/rpc/attach-volume-to-project",
    headers=headers,
    json={
        "volumeId": "<volume-id>",
        "projectId": "<project-id>"
    }
)
```

---

## Mount Paths

Mount paths depend on your **project type**. Check which exists in your execution to determine your project type.

### Git-Based Projects

| Volume Type | Mount Path |
|-------------|-----------|
| Live volume | `/mnt/netapp-volumes/<volume-name>/` |
| Snapshot by number | `/mnt/netapp-volumes/snapshots/<volume-name>/<snapshot-number>/` |
| Snapshot by tag | `/mnt/netapp-volumes/snapshot-tags/<volume-name>/<tag-name>/` |

### DFS (Domino File System) Projects

| Volume Type | Mount Path |
|-------------|-----------|
| Live volume | `/domino/netapp-volumes/<volume-name>/` |
| Snapshot by number | `/domino/netapp-volumes/snapshots/<volume-name>/<snapshot-number>/` |
| Snapshot by tag | `/domino/netapp-volumes/snapshot-tags/<volume-name>/<tag-name>/` |

### Snapshot Access Behavior

There are two ways to access snapshots, with an important behavioral difference:

- **`/snapshots/<volume-name>/<number>/`** — Accessed by snapshot number. When a new snapshot is taken while a workspace is running, the new numbered directory appears **immediately** in that workspace without a restart.
- **`/snapshot-tags/<volume-name>/<tag-name>/`** — Accessed by tag name. New snapshot-tag directories are **not** visible in a running workspace. You must **restart the workspace** to pick up newly created snapshot tags.

Use the numbered path when you need to access a fresh snapshot from within a live workspace. Use the tagged path for stable, named references in reproducible runs.

> **Important:** Only the most recently added snapshot tag is auto-mounted in executions. If a snapshot has multiple tags, only the newest tag is mounted.

> **Important:** Renaming a volume changes its mount path. Update any hardcoded paths in your code after renaming.

### Identify Your Project Type

```python
import os

if os.path.exists("/domino/netapp-volumes"):
    print("DFS Project")
    netapp_root = "/domino/netapp-volumes"
elif os.path.exists("/mnt/netapp-volumes"):
    print("Git-Based Project")
    netapp_root = "/mnt/netapp-volumes"
```

### Permissions

- **Owners/Editors**: Read-write access to the live volume
- **Readers**: Read-only access

### Example: Reading Data

```python
import pandas as pd

# Git-Based Project
df = pd.read_parquet("/mnt/netapp-volumes/large-training-data/features.parquet")

# DFS Project
df = pd.read_parquet("/domino/netapp-volumes/large-training-data/features.parquet")

# Read from a specific snapshot tag
df = pd.read_parquet("/mnt/netapp-volumes/snapshot-tags/large-training-data/v2.0/features.parquet")
```

### Example: Writing Data

```python
# Write directly to the live volume
df.to_parquet("/mnt/netapp-volumes/large-training-data/processed/output.parquet", index=False)

# List files
import os
files = os.listdir("/mnt/netapp-volumes/large-training-data/")
```

---

## Snapshots and Versioning

### What is a Snapshot?
A snapshot is a read-only, immutable record of the volume's data at a specific point in time. NetApp snapshots use redirect-on-write — no additional storage is consumed at creation time.

**Advantages over Domino Dataset snapshots:**
- Near-instant for any volume size (~3 seconds)
- Support commit messages for documentation and audit trails
- No storage overhead at creation time

### Create a Snapshot via UI
1. Go to project → **Data > NetApp Volumes**
2. Select the volume → click **Take Snapshot**
3. Add an optional **commit message** (e.g., "Added Q4 customer records")
4. Add an optional **tag name** (e.g., `v2.0`, `production`, `2024-Q4`)
5. Click **Confirm**

### Create a Snapshot via REST API
```python
# Create snapshot with description and one or more tags (tagNames is an array)
response = requests.post(
    f"{remotefs_url}/remotefs/v1/snapshots",
    headers=headers,
    json={
        "volumeId": "<volume-id>",
        "description": "Added Q4 customer records — 50M new rows",
        "tagNames": ["v2.0"]
    }
)
snapshot = response.json()
print(f"Snapshot ID: {snapshot['id']}")
```

### Add a Tag to an Existing Snapshot
```python
requests.post(
    f"{remotefs_url}/remotefs/v1/snapshots/{snapshot_id}/tags",
    headers=headers,
    json={"name": "production"}
)
```

### Create Snapshot After a Job Run
```python
# Snapshot tied to a specific Domino run for reproducibility
requests.post(
    f"{remotefs_url}/remotefs/v1/rpc/create-snapshot-from-run",
    headers=headers,
    json={
        "volumeId": "<volume-id>",
        "runId": "<domino-run-id>",
        "userId": "<user-id>",
        "description": "post-training-run-42"
    }
)
```

### Restore a Snapshot
```python
requests.post(
    f"{remotefs_url}/remotefs/v1/rpc/restore-snapshot",
    headers=headers,
    json={"snapshotId": "<snapshot-id>"}
)
```

---

## Roles and Permissions

| Role | API Value | Capabilities |
|------|-----------|-------------|
| **Reader** | `VolumeReader` | View files and snapshots; mount as read-only |
| **Editor** | `VolumeEditor` | All Reader capabilities + modify description, create/delete snapshots, manage shared access, manage users |
| **Owner** | `VolumeOwner` | All Editor capabilities + update volume grants, request deletion |

### Update Permissions via UI
1. Go to **Data > NetApp Volumes** → select volume
2. Click the three-dot menu → **Edit permissions**
3. Add/remove users and assign roles

### Update Permissions via REST API
```python
# targetRole values: "VolumeOwner", "VolumeEditor", "VolumeReader"
requests.put(
    f"{remotefs_url}/remotefs/v1/volumes/{volume_id}/grants",
    headers=headers,
    json=[
        {"targetId": "<user-id>", "targetRole": "VolumeEditor"},
        {"targetId": "<other-user-id>", "targetRole": "VolumeReader"}
    ]
)
```

---

## Using NetApp Volumes in Jobs

### Via Domino REST API
```python
requests.post(
    f"{api_url}/api/jobs/v1/jobs",
    headers=headers,
    json={
        "projectId": "<project-id>",
        "commandToRun": "python train.py",
        "hardwareTierId": "<hardware-tier-id>",
        "netAppVolumeIds": ["<volume-id>"]
    }
)
```

---

## Listing Volumes and Snapshots

```python
# List all volumes accessible to you
volumes = requests.get(
    f"{remotefs_url}/remotefs/v1/volumes",
    headers=headers
).json()

for v in volumes["data"]:
    capacity_tb = v["capacity"] / 1_000_000_000_000
    print(f"{v['name']} — {capacity_tb:.1f} TB — ID: {v['id']}")

# List snapshots for a volume
snapshots = requests.get(
    f"{remotefs_url}/remotefs/v1/snapshots",
    headers=headers,
    params={"volumeId": "<volume-id>"}
).json()

for s in snapshots["data"]:
    print(f"Snapshot {s['id']} v{s['version']} — {s.get('description', '')} — tags: {[t['name'] for t in s.get('tags', [])]}")
```

---

## Best Practices

### 1. Use Appropriate Storage
| Data Type | Storage |
|-----------|---------|
| Multi-TB shared datasets | NetApp Volume |
| Large training data (< 1 TB) | Domino Dataset |
| Model artifacts | MLflow artifact store or Domino Dataset |
| Code | Git/Project files |
| Temporary files | `/tmp/` |

### 2. Snapshot Before Changes
```python
# Always snapshot before modifying large volumes
requests.post(
    f"{remotefs_url}/remotefs/v1/snapshots",
    headers=headers,
    json={
        "volumeId": "<volume-id>",
        "description": "Pre-processing baseline snapshot",
        "tagNames": ["pre-processing-2024-01"]
    }
)

# Then run your data transformation
process_data()
```

### 3. Use Efficient File Formats
```python
# Parquet for tabular data (faster reads, smaller storage)
df.to_parquet("/mnt/netapp-volumes/dataset/data.parquet")

# Feather for fast pandas I/O
df.to_feather("/mnt/netapp-volumes/dataset/data.feather")

# HDF5 for large numerical arrays
import h5py
with h5py.File("/mnt/netapp-volumes/dataset/arrays.h5", "w") as f:
    f.create_dataset("features", data=features_array)
```

### 4. Organize Data
```
/mnt/netapp-volumes/my-volume/
├── raw/
│   ├── 2024-Q1/
│   └── 2024-Q2/
├── processed/
│   ├── features.parquet
│   └── labels.parquet
└── metadata/
    └── schema.json
```

### 5. Use Snapshot Tags for Reproducibility
Reference snapshot tags (not snapshot IDs) in your training scripts so that tagged paths remain stable across runs:
```python
# Reproducible reference using a tag
TRAINING_DATA = "/mnt/netapp-volumes/snapshot-tags/dataset/v2.0/"
df = pd.read_parquet(f"{TRAINING_DATA}/features.parquet")
```

### 6. Reading Large Volumes Efficiently
```python
import dask.dataframe as dd

# Lazy read — no data loaded until .compute()
df = dd.read_parquet("/mnt/netapp-volumes/dataset/large_data.parquet")
result = df.groupby("category").mean().compute()
```

---

## Troubleshooting

### Volume Not Found at Mount Path
- Verify the volume is added to the project (**Data > NetApp Volumes**)
- Confirm the volume name matches the path exactly (case-sensitive)
- Check that the workspace/job was started after the volume was added to the project
- Restart the workspace to pick up newly added volumes

### Permission Denied
- Check your role on the volume (need Editor or Owner to write)
- Verify you have been granted access by the volume owner
- For read-only snapshots, use the snapshot tag path instead of the live volume path

### Snapshot Tag Not Mounted
- Only the **most recently added** snapshot tag is auto-mounted
- Access older snapshot tags by their path directly: `/mnt/netapp-volumes/snapshot-tags/<name>/<tag>/`
- Verify the tag was created successfully via the UI or API

### No NetApp Filesystems Available
- Contact your Domino administrator — they must register NetApp ONTAP filesystems before volumes can be created
- Admins can register filesystems via **Admin > NetApp Volumes**

### Slow Read Performance
- Use columnar formats (Parquet, Feather) instead of CSV for tabular data
- Read only needed columns: `pd.read_parquet(path, columns=["col1", "col2"])`
- Use Dask or chunked reading for files larger than available RAM

---

## Documentation Reference
- [Work with NetApp Volumes](https://docs.dominodatalab.com/en/cloud/user_guide/06da1b/work-with-netapp-volumes/)
- [Create NetApp Volumes](https://docs.dominodatalab.com/en/cloud/user_guide/e6887f/create-netapp-volumes-from-domino-or-a-project/)
- [Add or Remove NetApp Volumes on Projects](https://docs.dominodatalab.com/en/cloud/user_guide/306570/add-or-remove-netapp-volumes-on-projects/)
- [View and Edit NetApp Volumes](https://docs.dominodatalab.com/en/cloud/user_guide/93fa12/view-and-edit-netapp-volumes/)
- [Version Data with Snapshots](https://docs.dominodatalab.com/en/cloud/user_guide/dbdbff/version-data-with-snapshots/)
- [NetApp Volumes REST API Reference](https://docs.dominodatalab.com/en/cloud/api_guide/b3b2a1/domino-netapp-volumes-api/)
- [Access Data in Domino (comparison guide)](https://docs.dominodatalab.com/en/cloud/user_guide/16d9c1/access-data-in-domino/)
