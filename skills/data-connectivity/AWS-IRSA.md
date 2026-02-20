# AWS IRSA (IAM Role for Service Accounts) for Domino

This guide covers configuring AWS IRSA to enable secure credential propagation for Domino workloads.

## What is IRSA?

IRSA (IAM Role for Service Accounts) enables Kubernetes workloads to assume AWS IAM roles securely using OpenID Connect (OIDC) authentication, eliminating the need for long-lived credentials.

### Benefits

- **No hardcoded credentials**: Eliminates static access keys
- **Short-lived tokens**: Automatic token rotation
- **Least privilege**: Fine-grained IAM policies
- **Audit trails**: Full CloudTrail logging
- **Cross-account access**: Support for multi-account architectures

### When to Use

Organizations should consider IRSA when:
- Security policy prohibits long-lived credentials
- Need IAM roles for all Domino workloads (Apps, Jobs, Workspaces)
- Require complex, rule-based role mappings
- Need cross-account role assumption

## How IRSA Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Domino         │────▶│  Kubernetes      │────▶│  AWS STS        │
│  Workload       │     │  Service Account │     │  AssumeRole     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐              │
                        │  OIDC Provider   │◀─────────────┘
                        │  (EKS/Kubernetes)│   Validates JWT
                        └──────────────────┘
```

### Flow:

1. **JWT Token Generation**: Kubernetes generates tokens via OIDC provider
2. **Token Mounting**: Tokens are projected as volumes in pods
3. **Web Identity Auth**: Workload calls `STS:AssumeRoleWithWebIdentity`
4. **Role Assumption**: AWS validates token and returns temporary credentials
5. **AWS Access**: Workload uses temporary credentials for AWS services

## Setup Steps

### Step 1: Enable OIDC Provider

For EKS clusters:

```bash
# Get OIDC issuer URL
aws eks describe-cluster \
  --name YOUR-CLUSTER-NAME \
  --query "cluster.identity.oidc.issuer" \
  --output text

# Create OIDC provider
eksctl utils associate-iam-oidc-provider \
  --cluster YOUR-CLUSTER-NAME \
  --approve
```

### Step 2: Create IAM Policy

Define permissions for your workloads:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket",
        "arn:aws:s3:::your-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateEndpoint",
        "sagemaker:InvokeEndpoint"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Create IAM Role with Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/oidc.eks.REGION.amazonaws.com/id/OIDC_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.REGION.amazonaws.com/id/OIDC_ID:sub": "system:serviceaccount:domino-compute:SERVICEACCOUNT_NAME"
        }
      }
    }
  ]
}
```

### Step 4: Create Kubernetes Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: domino-irsa-sa
  namespace: domino-compute
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/DominoWorkloadRole
```

### Step 5: Configure Domino Workloads

Domino uses a mutating webhook (Domsed) to inject IRSA configuration. Configure mutations based on:

- User identity
- Project
- Hardware tier
- Custom labels

## Using IRSA in Workloads

### Python with boto3

```python
import boto3

# No explicit credentials - IRSA provides them automatically
s3 = boto3.client('s3')

# List objects
response = s3.list_objects_v2(Bucket='my-bucket')
for obj in response.get('Contents', []):
    print(obj['Key'])

# Get object
response = s3.get_object(Bucket='my-bucket', Key='data.csv')
data = response['Body'].read()
```

### Access Other AWS Services

```python
import boto3

# SageMaker
sagemaker = boto3.client('sagemaker')

# DynamoDB
dynamodb = boto3.resource('dynamodb')

# Secrets Manager
secretsmanager = boto3.client('secretsmanager')
secret = secretsmanager.get_secret_value(SecretId='my-secret')

# Athena
athena = boto3.client('athena')
```

### Verify Credentials

```python
import boto3

# Check current identity
sts = boto3.client('sts')
identity = sts.get_caller_identity()

print(f"Account: {identity['Account']}")
print(f"ARN: {identity['Arn']}")
print(f"UserId: {identity['UserId']}")
```

## Role Mapping Strategies

### Per-User Roles

Map each Domino user to a specific IAM role:

```yaml
# Domsed mutation
mutations:
  - match:
      user: alice@company.com
    patch:
      serviceAccountName: alice-irsa-sa
```

### Per-Project Roles

Map roles based on Domino project:

```yaml
mutations:
  - match:
      project: sensitive-data-project
    patch:
      serviceAccountName: sensitive-data-sa
```

### Per-Hardware-Tier Roles

Different permissions for GPU workloads:

```yaml
mutations:
  - match:
      hardwareTier: gpu-large
    patch:
      serviceAccountName: gpu-workload-sa
```

## Cross-Account Access

### Trust Policy for Cross-Account

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::DOMINO_ACCOUNT:oidc-provider/oidc.eks.REGION.amazonaws.com/id/OIDC_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.REGION.amazonaws.com/id/OIDC_ID:sub": "system:serviceaccount:domino-compute:cross-account-sa"
        }
      }
    }
  ]
}
```

### Using Cross-Account Role

```python
import boto3

# Assume role in another account
sts = boto3.client('sts')
assumed = sts.assume_role(
    RoleArn='arn:aws:iam::OTHER_ACCOUNT:role/DataAccessRole',
    RoleSessionName='domino-workload'
)

# Use assumed credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=assumed['Credentials']['AccessKeyId'],
    aws_secret_access_key=assumed['Credentials']['SecretAccessKey'],
    aws_session_token=assumed['Credentials']['SessionToken']
)
```

## Troubleshooting

### Token Not Mounted

```bash
# Check pod for projected token
kubectl exec -it POD_NAME -n domino-compute -- ls -la /var/run/secrets/eks.amazonaws.com/serviceaccount/
```

### AssumeRoleWithWebIdentity Fails

```
An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity operation
```

**Solutions:**
1. Verify OIDC provider is correctly configured
2. Check trust policy conditions match exactly
3. Verify service account annotation
4. Check namespace matches trust policy

### Wrong Role Assumed

```python
# Debug: Check which role was assumed
sts = boto3.client('sts')
print(sts.get_caller_identity())
```

## Security Best Practices

1. **Least Privilege**: Grant minimum necessary permissions
2. **Session Duration**: Use short session durations
3. **Condition Keys**: Add extra conditions to trust policies
4. **Audit Logging**: Enable CloudTrail for all AssumeRole calls
5. **Regular Review**: Periodically audit role assignments

## Blueprint Reference

Complete implementation available at:
https://domino.ai/resources/blueprints/aws-irsa
