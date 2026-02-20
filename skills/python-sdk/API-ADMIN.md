# Domino Admin API

## Overview
The Admin API covers administrative endpoints for managing users, organizations, hardware tiers, data sources, and platform configuration.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Users API

### Get Current User
```
GET /api/users/v1/self
```

Get information about the authenticated user.

**Example:**
```python
response = requests.get(
    f"{base_url}/api/users/v1/self",
    headers=headers
)
user = response.json()
print(f"User: {user['userName']}")
print(f"Email: {user['email']}")
```

**Response:**
```json
{
  "id": "user-123",
  "userName": "jsmith",
  "email": "jsmith@company.com",
  "firstName": "John",
  "lastName": "Smith",
  "isAdmin": false
}
```

---

### List Users
```
GET /api/users/v1/users
```

Get all users visible to the current user.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |

---

### User Git Credentials
```
GET /api/users/beta/credentials/{userId}
```

Get Git credential accessor for a user.

### Update Git Credentials
```
PUT /api/users/v1/user/{userId}/tokenCredentials/{credentialId}
```

---

## Organizations API

### List Organizations
```
GET /api/organizations/v1/organizations
```

Get organizations for the current user.

**Example:**
```python
response = requests.get(
    f"{base_url}/api/organizations/v1/organizations",
    headers=headers
)
orgs = response.json()
```

---

### Create Organization
```
POST /api/organizations/v1/organizations
```

**Request Body:**
```json
{
  "name": "data-science-team",
  "description": "Data Science Team Organization"
}
```

---

### Get Organization
```
GET /api/organizations/v1/organizations/{organizationId}
```

---

### Get All Organizations (Admin)
```
GET /api/organizations/v1/organizations/all
```

Only accessible to admin users.

---

### Add User to Organization
```
PUT /api/organizations/v1/organizations/{organizationId}/user
```

**Request Body:**
```json
{
  "userId": "user-456",
  "role": "Member"
}
```

---

### Remove User from Organization
```
DELETE /api/organizations/v1/organizations/{organizationId}/user
```

**Request Body:**
```json
{
  "userId": "user-456"
}
```

---

## Hardware Tiers API

### List Hardware Tiers
```
GET /api/hardwaretiers/v1/hardwaretiers
```

Get all available hardware tiers.

**Example:**
```python
response = requests.get(
    f"{base_url}/api/hardwaretiers/v1/hardwaretiers",
    headers=headers
)
tiers = response.json()

for tier in tiers['data']:
    print(f"{tier['name']}: {tier['cores']} cores, {tier['memoryMb']}MB RAM")
```

**Response:**
```json
{
  "data": [
    {
      "id": "tier-123",
      "name": "small",
      "cores": 2,
      "memoryMb": 8192,
      "gpuCount": 0,
      "isDefault": false
    },
    {
      "id": "tier-456",
      "name": "gpu-large",
      "cores": 8,
      "memoryMb": 32768,
      "gpuCount": 1,
      "gpuType": "nvidia-tesla-v100"
    }
  ]
}
```

---

### Get Hardware Tier
```
GET /api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}
```

---

### Create Hardware Tier (Admin)
```
POST /api/hardwaretiers/v1/hardwaretiers
```

**Request Body:**
```json
{
  "name": "custom-large",
  "cores": 16,
  "memoryMb": 65536,
  "gpuCount": 2
}
```

---

### Update Hardware Tier (Admin)
```
PUT /api/hardwaretiers/v1/hardwaretiers
```

---

### Archive Hardware Tier (Admin)
```
DELETE /api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}
```

---

## Data Sources API

### List Data Sources
```
GET /api/datasource/v1/datasources
```

Get all active data sources the user has access to.

**Example:**
```python
response = requests.get(
    f"{base_url}/api/datasource/v1/datasources",
    headers=headers
)
sources = response.json()
```

---

### Create Data Source
```
POST /api/datasource/v1/datasources
```

**Request Body:**
```json
{
  "name": "postgres-prod",
  "type": "PostgreSQL",
  "config": {
    "host": "db.company.com",
    "port": 5432,
    "database": "analytics"
  }
}
```

---

### Get Data Source
```
GET /api/datasource/v1/datasources/{dataSourceId}
```

---

### Update Data Source
```
PATCH /api/datasource/v1/datasources/{dataSourceId}
```

---

### Delete Data Source
```
DELETE /api/datasource/v1/datasources/{dataSourceId}
```

---

### Data Source Audit
```
GET /api/datasource/v1/audit
```

Get audit logs for data source access.

---

## Service Accounts API

### List Service Accounts
```
GET /api/serviceAccounts/v1/serviceAccounts
```

---

### Create Service Account
```
POST /api/serviceAccounts/v1/serviceAccounts
```

**Request Body:**
```json
{
  "name": "ci-cd-service",
  "description": "Service account for CI/CD pipelines"
}
```

---

### Create Token
```
POST /api/serviceAccounts/v1/serviceAccounts/{serviceAccountId}/tokens
```

Create API token for service account.

---

### List Tokens
```
GET /api/serviceAccounts/v1/serviceAccounts/{serviceAccountId}/tokens
```

---

## Deployment Targets API (Admin)

### List Deployment Target Types
```
GET /api/admin/v1/deploymentTargetTypes
```

### Get Deployment Target Type
```
GET /api/admin/v1/deploymentTargetTypes/{typeId}
```

### List Deployment Targets
```
GET /api/admin/v1/deploymentTargets
```

### Create Deployment Target
```
POST /api/admin/v1/deploymentTargets
```

### Get Deployment Target
```
GET /api/admin/v1/deploymentTargets/{targetId}
```

### Update Deployment Target
```
PATCH /api/admin/v1/deploymentTargets/{targetId}
```

### Delete Deployment Target
```
DELETE /api/admin/v1/deploymentTargets/{targetId}
```

---

## Resource Configurations

### List Resource Configurations
```
GET /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations
```

### Create Resource Configuration
```
POST /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations
```

### Get Resource Configuration
```
GET /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations/{configId}
```

### Update Resource Configuration
```
PATCH /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations/{configId}
```

### Delete Resource Configuration
```
DELETE /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations/{configId}
```

---

## Cost API

### Get Cost Allocation
```
GET /api/cost/v1/allocation
```

Get detailed cost breakdown.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `startTime` | string | ISO 8601 start time |
| `endTime` | string | ISO 8601 end time |
| `aggregateBy` | string | user, project, organization |

**Example:**
```python
response = requests.get(
    f"{base_url}/api/cost/v1/allocation",
    headers=headers,
    params={
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2024-01-31T23:59:59Z",
        "aggregateBy": "project"
    }
)
costs = response.json()
```

---

### Get Cost Summary
```
GET /api/cost/v1/allocation/summary
```

Faster summary-level cost data.

---

### Get Asset Costs
```
GET /api/cost/v1/asset
```

---

## Billing Tags

### List Billing Tags
```
GET /api/cost/v1/billingtags
```

### Create/Update Billing Tags
```
POST /api/cost/v1/billingtags
```

### Billing Tag Settings
```
GET /api/cost/v1/billingtagSettings
PUT /api/cost/v1/billingtagSettings
```

### Billing Tag Mode
```
GET /api/cost/v1/billingtagSettings/mode
PUT /api/cost/v1/billingtagSettings/mode
```

---

## Audit Events API

### Get Audit Events
```
GET /auditevents
```

Get platform audit events.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `startTime` | string | Filter start |
| `endTime` | string | Filter end |
| `eventType` | string | Filter by event type |

**Example:**
```python
response = requests.get(
    f"{base_url}/auditevents",
    headers=headers,
    params={
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2024-01-02T00:00:00Z"
    }
)
events = response.json()
```

---

## Common Admin Tasks

### Create Service Account for CI/CD
```python
# Create service account
response = requests.post(
    f"{base_url}/api/serviceAccounts/v1/serviceAccounts",
    headers=headers,
    json={
        "name": "github-actions",
        "description": "Service account for GitHub Actions"
    }
)
sa = response.json()
sa_id = sa['id']

# Create API token
response = requests.post(
    f"{base_url}/api/serviceAccounts/v1/serviceAccounts/{sa_id}/tokens",
    headers=headers,
    json={"description": "CI/CD token"}
)
token = response.json()
print(f"API Token: {token['token']}")  # Save this securely!
```

### Get Platform Usage Report
```python
# Get cost allocation by user
response = requests.get(
    f"{base_url}/api/cost/v1/allocation",
    headers=headers,
    params={
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2024-01-31T23:59:59Z",
        "aggregateBy": "user"
    }
)
usage = response.json()

for user in usage['data']:
    print(f"{user['name']}: ${user['totalCost']:.2f}")
```
