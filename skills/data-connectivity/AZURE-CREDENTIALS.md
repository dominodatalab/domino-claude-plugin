# Azure Entra ID Credential Propagation for Domino

This guide covers configuring Azure Entra ID (formerly Azure Active Directory) for user-based credential propagation in Domino workloads.

## Overview

Azure Entra ID authentication enables OAuth-based access to Azure data services, providing:
- User-level audit trails for data access
- Centrally-managed role-based access control (RBAC)
- Secure access without storing credentials in code

### Use Cases

- Access Azure Data Lake Storage Gen2
- Query Azure Synapse Analytics
- Connect to Azure SQL Database
- Access Azure Blob Storage
- Use Azure Machine Learning services

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Domino         │────▶│  Azure Entra     │────▶│  Azure Data     │
│  Workload       │     │  ID (OAuth)      │     │  Services       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
   User identity           Access token
   propagated              issued
```

### Flow:

1. User starts Domino workload
2. Domino propagates user identity to Azure Entra
3. Azure Entra validates and issues access token
4. Workload uses token to access Azure services
5. All access logged under user's identity

## Prerequisites

- Azure subscription with Entra ID
- Domino configured with Azure AD SSO
- App registration in Azure
- Required API permissions configured

## Setup Steps

### Step 1: Create App Registration

1. Go to Azure Portal → Azure Active Directory
2. Navigate to **App registrations** → **New registration**
3. Configure:
   - **Name**: Domino Credential Propagation
   - **Supported account types**: Single tenant
   - **Redirect URI**: Web, `https://your-domino.com/callback`

### Step 2: Configure API Permissions

Add required permissions:

```
Microsoft Graph:
- User.Read (Delegated)
- offline_access (Delegated)

Azure Storage:
- user_impersonation (Delegated)

Azure Data Lake:
- user_impersonation (Delegated)
```

### Step 3: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Set expiration and save the secret value

### Step 4: Configure Domino

Add Azure AD configuration to Domino:

```yaml
azure:
  tenantId: "your-tenant-id"
  clientId: "your-app-client-id"
  clientSecret: "${AZURE_CLIENT_SECRET}"
  scopes:
    - "https://storage.azure.com/.default"
    - "https://database.windows.net/.default"
```

## Using Azure Credentials in Workloads

### Access Azure Blob Storage

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Credential propagation - uses logged-in user's identity
credential = DefaultAzureCredential()

blob_service = BlobServiceClient(
    account_url="https://mystorageaccount.blob.core.windows.net",
    credential=credential
)

# List containers
containers = blob_service.list_containers()
for container in containers:
    print(container['name'])
```

### Access Azure Data Lake Storage Gen2

```python
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

credential = DefaultAzureCredential()

datalake_service = DataLakeServiceClient(
    account_url="https://mystorageaccount.dfs.core.windows.net",
    credential=credential
)

# Access file system
file_system = datalake_service.get_file_system_client("myfilesystem")
paths = file_system.get_paths()
for path in paths:
    print(path.name)
```

### Access Azure SQL Database

```python
from azure.identity import DefaultAzureCredential
import pyodbc
import struct

credential = DefaultAzureCredential()

# Get access token for Azure SQL
token = credential.get_token("https://database.windows.net/.default")

# Build token struct for pyodbc
token_bytes = token.token.encode("UTF-16-LE")
token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

# Connect with token
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=myserver.database.windows.net;"
    "DATABASE=mydatabase;",
    attrs_before={1256: token_struct}  # SQL_COPT_SS_ACCESS_TOKEN
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM mytable")
```

### Access Azure Synapse Analytics

```python
from azure.identity import DefaultAzureCredential
from pyspark.sql import SparkSession

credential = DefaultAzureCredential()
token = credential.get_token("https://database.windows.net/.default")

spark = SparkSession.builder.getOrCreate()

# Configure Synapse connection
spark.conf.set(
    "fs.azure.account.oauth2.client.endpoint.mystorageaccount.dfs.core.windows.net",
    f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
)

# Read from Synapse
df = spark.read \
    .format("com.databricks.spark.sqldw") \
    .option("url", "jdbc:sqlserver://myworkspace.sql.azuresynapse.net:1433") \
    .option("tempDir", "abfss://container@storage.dfs.core.windows.net/temp") \
    .option("forwardSparkAzureStorageCredentials", "true") \
    .option("dbTable", "myschema.mytable") \
    .load()
```

### With pandas

```python
from azure.identity import DefaultAzureCredential
import pandas as pd
from io import StringIO

credential = DefaultAzureCredential()

# Read CSV from blob storage
from azure.storage.blob import BlobClient
blob = BlobClient(
    account_url="https://mystorageaccount.blob.core.windows.net",
    container_name="data",
    blob_name="sales.csv",
    credential=credential
)

content = blob.download_blob().content_as_text()
df = pd.read_csv(StringIO(content))
```

## Role-Based Access Control

### Azure Storage RBAC Roles

| Role | Permissions |
|------|-------------|
| Storage Blob Data Reader | Read blobs |
| Storage Blob Data Contributor | Read, write, delete blobs |
| Storage Blob Data Owner | Full access including RBAC |

### Assign Role to User

```bash
az role assignment create \
  --role "Storage Blob Data Reader" \
  --assignee user@company.com \
  --scope /subscriptions/SUB_ID/resourceGroups/RG/providers/Microsoft.Storage/storageAccounts/ACCOUNT
```

## Troubleshooting

### Authentication Errors

```
ClientAuthenticationError: DefaultAzureCredential failed to retrieve a token
```

**Solutions:**
1. Verify user is logged into Domino with Azure AD
2. Check app registration permissions
3. Verify tenant ID is correct
4. Check client secret hasn't expired

### Permission Denied

```
AuthorizationPermissionMismatch: The request is not authorized to perform this operation
```

**Solutions:**
1. Verify user has required RBAC role
2. Check role assignment scope
3. Allow time for role propagation (up to 5 minutes)

### Token Expired

```
ExpiredAuthenticationToken: The access token expiry UTC time is earlier than current UTC time
```

**Solutions:**
1. Refresh the credential
2. Check `offline_access` permission is granted
3. Verify token refresh is configured

## Security Best Practices

1. **Least Privilege**: Assign minimum required RBAC roles
2. **Scope Appropriately**: Use resource-level role assignments
3. **Audit Access**: Enable Azure Monitor diagnostic settings
4. **Rotate Secrets**: Set short client secret expiration
5. **Conditional Access**: Apply Azure AD conditional access policies

## Blueprint Reference

Complete implementation available at:
https://domino.ai/resources/blueprints/domino-azure-credential-propagation
