---
name: domino-data-connectivity
description: Connect Domino workloads to external data sources including AWS S3 (via Mountpoint CSI driver), credential propagation with AWS IRSA and Azure Entra ID, and External Data Volumes. Use when configuring S3 access, setting up credential propagation, or connecting to cloud data sources from Domino.
---

# Domino Data Connectivity Skill

This skill provides comprehensive knowledge for connecting Domino workloads to external data sources, including AWS S3, Azure storage, and credential propagation.

## Key Concepts

### Data Access Options in Domino

| Option | Use Case |
|--------|----------|
| **Datasets** | Project-level data storage |
| **Data Sources** | External database connections |
| **External Data Volumes (EDV)** | Mount external storage as volumes |
| **S3 Mountpoint** | Direct S3 access as file system |
| **Credential Propagation** | Pass user identity to cloud services |

### Credential Propagation Methods

| Method | Cloud | Description |
|--------|-------|-------------|
| **IRSA** | AWS | IAM Role for Service Accounts via OIDC |
| **Azure Entra ID** | Azure | User-based credential propagation |

## Related Documentation

- [S3-MOUNTPOINT.md](./S3-MOUNTPOINT.md) - AWS S3 as local file system
- [AWS-IRSA.md](./AWS-IRSA.md) - AWS IAM Role for Service Accounts
- [AZURE-CREDENTIALS.md](./AZURE-CREDENTIALS.md) - Azure Entra ID integration

## Quick Start

### Accessing S3 Data

With Mountpoint S3 configured, access S3 as a local file system:

```python
import pandas as pd

# S3 data appears as local files
df = pd.read_parquet("/mnt/s3-data/datasets/sales.parquet")
```

### Using IRSA for AWS Services

With IRSA configured, AWS SDK uses automatic credentials:

```python
import boto3

# No explicit credentials needed - IRSA provides them
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='my-bucket')
```

### Accessing External Data Volumes

EDVs are mounted at configured paths:

```python
# Read from external volume
with open("/mnt/external-data/config.json") as f:
    config = json.load(f)
```

## When to Use Each Option

### Use S3 Mountpoint When:
- Working with large datasets stored in S3
- Need file system interface to S3
- Want to avoid EFS costs for large data
- Require multi-region data access

### Use IRSA When:
- Need AWS service access from Domino workloads
- Policy prohibits long-lived credentials
- Require user-level audit trails
- Need cross-account role assumption

### Use Azure Entra When:
- Working with Azure data services
- Need OAuth-based authentication
- Require user-level access control
- Need centralized RBAC

## Blueprint References

- [S3 Mountpoint Blueprint](https://domino.ai/resources/blueprints/transforming-s3-into-local-storage)
- [AWS IRSA Blueprint](https://domino.ai/resources/blueprints/aws-irsa)
- [Azure Credential Propagation Blueprint](https://domino.ai/resources/blueprints/domino-azure-credential-propagation)

## GitHub Repository

Implementation templates available at:
https://github.com/dominodatalab/domino-blueprints
