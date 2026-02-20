# Domino Apps API

## Overview
The Apps API allows you to create, manage, and deploy web applications in Domino.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Endpoints

### List Apps
```
GET /api/apps/beta/apps
```

Get apps visible to the user.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `projectId` | string | Filter by project |
| `status` | string | Filter by status |
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |

**Status Values:**
- `Running`
- `Stopped`
- `Starting`
- `Failed`

**Example:**
```python
response = requests.get(
    f"{base_url}/api/apps/beta/apps",
    headers=headers,
    params={
        "status": "Running",
        "limit": 20
    }
)
apps = response.json()
```

**Response:**
```json
{
  "data": [
    {
      "id": "app-123",
      "name": "Dashboard App",
      "description": "Sales analytics dashboard",
      "projectId": "project-456",
      "status": "Running",
      "url": "https://your-domino.com/apps/app-123",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ],
  "offset": 0,
  "limit": 20,
  "totalCount": 5
}
```

---

### Create App
```
POST /api/apps/beta/apps
```

Create a new application.

**Request Body:**
```json
{
  "projectId": "project-123",
  "name": "analytics-dashboard",
  "description": "Real-time analytics dashboard",
  "hardwareTierId": "small",
  "environmentId": "env-789"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/apps/beta/apps",
    headers=headers,
    json={
        "projectId": "project-123",
        "name": "customer-insights",
        "description": "Customer analytics dashboard",
        "hardwareTierId": "small",
        "environmentId": "env-789"
    }
)
app = response.json()
print(f"Created app: {app['id']}")
print(f"URL: {app['url']}")
```

---

### Get App
```
GET /api/apps/beta/apps/{appId}
```

**Example:**
```python
app_id = "app-123"
response = requests.get(
    f"{base_url}/api/apps/beta/apps/{app_id}",
    headers=headers
)
app = response.json()
```

---

### Update App
```
PATCH /api/apps/beta/apps/{appId}
```

Update app metadata.

**Request Body:**
```json
{
  "name": "new-name",
  "description": "Updated description"
}
```

---

### Delete App
```
DELETE /api/apps/beta/apps/{appId}
```

---

## App Versions

### List Versions
```
GET /api/apps/beta/apps/{appId}/versions
```

Get all versions of an app.

### Create New Version
```
POST /api/apps/beta/apps/{appId}/versions
```

Publish a new version of the app.

**Request Body:**
```json
{
  "hardwareTierId": "medium",
  "environmentId": "env-789"
}
```

### Get Version
```
GET /api/apps/beta/apps/{appId}/versions/{versionId}
```

### Update Version
```
PATCH /api/apps/beta/apps/{appId}/versions/{versionId}
```

---

## App Instances

### List Instances
```
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances
```

Get running instances of an app version.

### Get Instance
```
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}
```

### Delete Instance
```
DELETE /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}
```

Stop and remove an app instance.

### Get Instance Logs
```
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}/logs
```

**Example:**
```python
response = requests.get(
    f"{base_url}/api/apps/beta/apps/{app_id}/versions/{version_id}/instances/{instance_id}/logs",
    headers=headers
)
logs = response.text
print(logs)
```

### Get Real-Time Logs
```
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}/realTimeLogs
```

Stream logs in real-time.

### Record View
```
POST /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}/views
```

Record an app view for analytics.

---

## App Thumbnail

### Get Thumbnail
```
GET /api/apps/beta/apps/{appId}/thumbnail
```

### Upload Thumbnail
```
POST /api/apps/beta/apps/{appId}/thumbnail
```

Upload a thumbnail image for the app.

### Delete Thumbnail
```
DELETE /api/apps/beta/apps/{appId}/thumbnail
```

### Get Thumbnail Metadata
```
GET /api/apps/beta/apps/{appId}/thumbnail/metadata
```

---

## App Views Analytics

### Get Views
```
GET /api/apps/beta/apps/{appId}/views
```

Get view statistics for an app.

**Query Parameters:**
- `startTime`: Filter start timestamp
- `endTime`: Filter end timestamp

---

## Vanity URLs

### Get by Vanity URL
```
GET /api/apps/beta/apps/vanityUrls/{vanityUrl}
```

Look up an app by its vanity URL.

---

## Filter Options

### Get Project Filter Options
```
GET /api/apps/beta/apps/projectFilterOptions
```

Get list of projects that have apps.

### Get Publisher Filter Options
```
GET /api/apps/beta/apps/publisherFilterOptions
```

Get list of users who have published apps.

---

## Access Requests

### Request Access
```
POST /api/apps/beta/apps/{appId}/access/requests
```

Request access to a private app.

---

## Complete Workflow Example

```python
import requests
import time

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"

# 1. Create app
response = requests.post(
    f"{base_url}/api/apps/beta/apps",
    headers=headers,
    json={
        "projectId": "project-123",
        "name": "ml-dashboard",
        "description": "Machine learning model dashboard",
        "hardwareTierId": "small",
        "environmentId": "env-789"
    }
)
app = response.json()
app_id = app['id']
print(f"Created app: {app_id}")

# 2. Wait for app to start
while True:
    response = requests.get(
        f"{base_url}/api/apps/beta/apps/{app_id}",
        headers=headers
    )
    status = response.json()['status']

    if status == 'Running':
        print(f"App is running!")
        break
    elif status == 'Failed':
        print("App failed to start")
        break
    else:
        print(f"Status: {status}")
        time.sleep(10)

# 3. Get app URL
response = requests.get(
    f"{base_url}/api/apps/beta/apps/{app_id}",
    headers=headers
)
app_url = response.json()['url']
print(f"App URL: {app_url}")

# 4. View logs
versions = requests.get(
    f"{base_url}/api/apps/beta/apps/{app_id}/versions",
    headers=headers
).json()
version_id = versions['data'][0]['id']

instances = requests.get(
    f"{base_url}/api/apps/beta/apps/{app_id}/versions/{version_id}/instances",
    headers=headers
).json()
instance_id = instances['data'][0]['id']

logs = requests.get(
    f"{base_url}/api/apps/beta/apps/{app_id}/versions/{version_id}/instances/{instance_id}/logs",
    headers=headers
).text
print(f"Logs:\n{logs}")

# 5. Stop app (delete instance)
requests.delete(
    f"{base_url}/api/apps/beta/apps/{app_id}/versions/{version_id}/instances/{instance_id}",
    headers=headers
)
print("App stopped")
```

---

## App Types and Configuration

Apps in Domino require:
1. **app.sh**: Launch script that starts the app
2. **Proper host binding**: Bind to `0.0.0.0`
3. **Environment**: With required dependencies

Example `app.sh` for Streamlit:
```bash
#!/bin/bash
streamlit run app.py --server.port 8888 --server.address 0.0.0.0
```

Example for React/Vite:
```bash
#!/bin/bash
npm run build
npm run preview -- --host 0.0.0.0 --port 8888
```
