# Domino Admin API

## Overview
The Admin API covers administrative endpoints for managing users, organizations, hardware tiers, data sources, and platform configuration.

## Authentication

https://docs.domino.ai/cloud/reference/api/domino-api-authentication

Same in-run patterns as [SKILL.md](SKILL.md#authentication): prefer `DOMINO_API_PROXY` with no header (5.4.0+ with JWT credential propagation); else access-token + `DOMINO_USER_HOST`. Examples below use this setup. Member-visible vs platform-admin routes still return **403** when the starting user lacks permission.

```python
import os
import requests

if os.environ.get("DOMINO_API_PROXY"):
    base_url = os.environ["DOMINO_API_PROXY"].rstrip("/")
    headers = {}
else:
    base_url = (os.environ.get("DOMINO_USER_HOST") or os.environ.get("DOMINO_API_HOST") or "").rstrip("/")
    token = requests.get("http://localhost:8899/access-token").text.strip()
    headers = {"Authorization": f"Bearer {token}"}
```

**Outside a run:** code on your laptop or in CI is not in a Domino container. Use the browser-facing deployment HTTPS URL (not localhost sidecar hosts) and `Authorization: Bearer` with a PAT (you) or service account token (automation). Details: [SKILL.md](SKILL.md#outside-a-run-laptop-ci-cron-outside-domino).

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

**Org pseudo-users:** Each organization has an `organizationUserId` user row. `GET /api/users/v1/users` can return those rows mixed with human users and service accounts. There is **no** `listOnlyUsers` query param on that route today.

`GET /v4/users` (`listUsers`) accepts `listOnlyUsers=true` to drop org pseudo-users when `/v4/users` is reachable from your run. Client-side filtering or org diff may still be needed. See https://dominodatalab.atlassian.net/browse/DOM-80329

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

### User roles
```
GET /api/users/v1/user/{userId}/roles
PUT /api/users/v1/user/{userId}/roles
```

Requires admin privileges to read or update another user's roles.

---

### User lifecycle (deactivation)

| Surface | Route | Notes |
|---------|-------|-------|
| Service accounts | `POST /api/serviceAccounts/v1/serviceAccounts/{id}/deactivate` | Deactivates SA identity |
| Human users | Admin UI / nucleus flows | No single standard REST deactivate-user path documented for automation; confirm swagger on your deployment |

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

**Visitor JWT / apps:** Published apps often call org list because visitor JWTs lack org claims. That pattern requires the app owner to be a Domino admin and is fragile; prefer documented identity flows for new apps (see `identity_in_app_container.py` in api-improvements doc-examples).

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

## Central config (platform settings, not feature flags)

Admin key/value settings for deployment configuration. **Not** the same system as user-facing feature flags.

| Method | Path |
|--------|------|
| GET | `/v4/admin/centralConfigSettings` |
| POST | `/v4/admin/centralConfigSettings` |
| PUT | `/v4/admin/centralConfigSettings/{id}` |
| DELETE | `/v4/admin/centralConfigSettings/{id}` |

Secrets are obfuscated on read. Only three keys overlap feature flags via `SettingsToFeatureFlagConverter`; do not use central config as a bulk feature-flag export.

---

## Feature flags (effective per caller only)

| Route | What you get |
|-------|----------------|
| `GET /v4/auth/principal` | Enabled feature flags **for the authenticated principal only** |

There is no bulk list-all-flags-and-overrides REST surface today. Admin UI owns create/update for overrides.

---

## Cost API

Permissions vary by deployment; cost admin operations may require platform admin or billing roles not spelled out in every operation description. Dataset storage cost and domino-cost budgets live on additional `/v4/...` routes (`/v4/datasetrw/dataset-cost`, `/v4/domino-cost/budgets`); there is no single unified cost summary API. Verify 403 responses against your caller's admin/billing role before retrying.

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
