# AWS S3 Mountpoint Integration for Domino

This guide covers setting up AWS Mountpoint for Amazon S3 to provide file system access to S3 data within Domino workloads.

## Overview

AWS Mountpoint for Amazon S3 CSI driver enables mounting S3 buckets as local file systems in Kubernetes pods, including Domino workspaces, jobs, and apps.

### Benefits

- **Cost-effective storage**: Direct S3 access without EFS overhead
- **Familiar interface**: File browsing just like local storage
- **Scalability**: Access massive datasets without copying
- **Security**: No privileged container access required

### When to Use

**Ideal for:**
- Large datasets that would be expensive in EFS
- Read-heavy workloads
- Multi-region data access
- Security-conscious environments

**Not recommended for:**
- Write-heavy workloads
- Small, frequently-accessed datasets
- Workloads requiring low-latency access

## Architecture

```
┌─────────────────────┐
│   Domino Workload   │
│   (Workspace/Job)   │
├─────────────────────┤
│  /mnt/s3-data/      │  ← Mounted S3 bucket
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │  CSI Driver  │
    │  (Node-level)│
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  AWS S3      │
    │  Bucket      │
    └─────────────┘
```

## Setup Steps

### Step 1: IAM Configuration

Create IAM policy for S3 access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MountpointFullBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    },
    {
      "Sid": "MountpointFullObjectAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

### Step 2: Create Service Account

Using eksctl:

```bash
eksctl create iamserviceaccount \
  --name s3-csi-driver-sa \
  --namespace kube-system \
  --cluster YOUR-CLUSTER-NAME \
  --attach-policy-arn arn:aws:iam::ACCOUNT_ID:policy/S3CSIDriverPolicy \
  --approve \
  --override-existing-serviceaccounts
```

### Step 3: Install CSI Driver

Using Helm:

```bash
helm repo add aws-mountpoint-s3-csi-driver \
  https://awslabs.github.io/mountpoint-s3-csi-driver

helm install aws-mountpoint-s3-csi-driver \
  aws-mountpoint-s3-csi-driver/aws-mountpoint-s3-csi-driver \
  --namespace kube-system \
  --set controller.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::ACCOUNT_ID:role/S3CSIDriverRole
```

### Step 4: Create PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: s3-pv
spec:
  capacity:
    storage: 1Ti  # Arbitrary, S3 is unlimited
  accessModes:
    - ReadWriteMany
  mountOptions:
    - allow-delete
    - region us-east-1
    - uid=12574
    - gid=12574
  csi:
    driver: s3.csi.aws.com
    volumeHandle: s3-csi-driver-volume
    volumeAttributes:
      bucketName: YOUR-BUCKET-NAME
```

### Step 5: Create PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: s3-pvc
  namespace: domino-compute
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: ""
  resources:
    requests:
      storage: 1Ti
  volumeName: s3-pv
```

### Step 6: Configure Domino EDV

Create an External Data Volume in Domino:

1. Go to **Admin** → **External Data Volumes**
2. Click **New External Data Volume**
3. Configure:
   - **Name**: s3-data
   - **Mount Path**: /mnt/s3-data
   - **PVC Name**: s3-pvc
   - **Namespace**: domino-compute

## Using S3 Mountpoint in Workloads

### Reading Data

```python
import pandas as pd

# S3 bucket mounted at /mnt/s3-data
df = pd.read_csv("/mnt/s3-data/datasets/sales.csv")

# Read parquet
df = pd.read_parquet("/mnt/s3-data/datasets/large_dataset.parquet")

# List files
import os
files = os.listdir("/mnt/s3-data/datasets/")
```

### Writing Data

```python
# Write results back to S3
df.to_parquet("/mnt/s3-data/outputs/results.parquet")

# Save model artifacts
import joblib
joblib.dump(model, "/mnt/s3-data/models/model.joblib")
```

### With Spark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Read from mounted S3
df = spark.read.parquet("/mnt/s3-data/datasets/")

# Process and write back
df_processed = df.filter(...)
df_processed.write.parquet("/mnt/s3-data/outputs/")
```

## Mount Options

| Option | Description |
|--------|-------------|
| `region` | AWS region of the bucket |
| `uid` | User ID for file ownership |
| `gid` | Group ID for file ownership |
| `allow-delete` | Enable file deletion |
| `allow-other` | Allow access by other users |
| `prefix` | Mount only a specific prefix |

### Example with Prefix

Mount only a specific folder:

```yaml
mountOptions:
  - region us-east-1
  - prefix=datasets/sales/
```

## Performance Considerations

### Read Performance

- First access may have higher latency
- Subsequent reads benefit from caching
- Sequential reads perform better than random

### Write Performance

- Writes are uploaded on close
- Large files uploaded in parts
- Consider buffering for small writes

### Optimization Tips

1. Use Parquet or other columnar formats
2. Partition large datasets
3. Avoid many small files
4. Use appropriate file sizes (100MB-1GB)

## Troubleshooting

### Mount Failures

```bash
# Check CSI driver pods
kubectl get pods -n kube-system | grep mountpoint

# Check driver logs
kubectl logs -n kube-system -l app=aws-mountpoint-s3-csi-driver
```

### Permission Errors

```
Error: Access Denied
```

**Solutions:**
1. Verify IAM policy is correct
2. Check service account annotation
3. Verify bucket name is correct
4. Check uid/gid mount options

### Slow Performance

1. Check network connectivity to S3
2. Verify bucket is in same region
3. Consider using S3 Transfer Acceleration
4. Use larger files to reduce overhead

## Security

### Least Privilege

Only grant necessary S3 permissions:

```json
{
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ]
}
```

### Bucket Policies

Combine with bucket policies for additional control:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/S3CSIDriverRole"
      },
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::bucket/*"
    }
  ]
}
```

## Blueprint Reference

Complete implementation available at:
https://github.com/dominodatalab/domino-blueprints/tree/main/mountpoint-s3
