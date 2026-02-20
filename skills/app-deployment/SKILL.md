---
name: domino-app-deployment
description: Deploy web applications to Domino Data Lab with expertise in React apps (Vite) behind Domino's reverse proxy. Covers app.sh configuration, port configuration, base path handling for SPAs, CI/CD with GitHub Actions, and proxy troubleshooting. Use when deploying apps to Domino, setting up CI/CD pipelines, fixing broken routing, or configuring JavaScript frameworks for Domino's proxy.
---

# Domino App Deployment Skill

This skill provides comprehensive knowledge for deploying web applications to Domino Data Lab, with special focus on React applications using Vite.

## Key Concepts

### Domino App Architecture

Domino apps run in containers behind a reverse proxy that:
1. Authenticates users via Domino's auth system
2. Strips the URL prefix before forwarding to your app
3. Routes traffic to your app container
4. Handles infrastructure provisioning, routing, and resource management

**Note:** Port selection is flexible; port 8888 is no longer required. You can use any port your application prefers.

### Critical Configuration Points

1. **Host Binding**: Bind to `0.0.0.0` (not localhost) so Domino can reach your app
2. **Relative Base Path**: Use `base: './'` in Vite config for React apps
3. **app.sh**: Entry point script (launch file) that Domino executes

## Related Documentation

- [REACT-VITE-GUIDE.md](./REACT-VITE-GUIDE.md) - Deep dive into Vite + React configuration
- [REACT-CICD.md](./REACT-CICD.md) - CI/CD setup with GitHub Actions
- [FRAMEWORKS.md](./FRAMEWORKS.md) - Streamlit, Dash, Flask configurations
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions

## Quick Start

### React with Vite

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',  // CRITICAL for Domino proxy
  server: { host: '0.0.0.0', port: 8888, strictPort: true },
  preview: { host: '0.0.0.0', port: 8888, strictPort: true },
})
```

```bash
# app.sh
#!/bin/bash
set -e
cd /mnt/code
npm ci
npm run build
npx serve -s dist -l 8888 --no-clipboard
```

### Streamlit

```bash
# app.sh
#!/bin/bash
streamlit run app.py --server.port 8888 --server.address 0.0.0.0
```

### Dash/Flask

```bash
# app.sh
#!/bin/bash
python app.py  # Must bind to 0.0.0.0:8888
```

## Environment Variables

Domino provides these environment variables to your app:

| Variable | Description |
|----------|-------------|
| `DOMINO_PROJECT_NAME` | Current project name |
| `DOMINO_PROJECT_OWNER` | Project owner username |
| `DOMINO_RUN_ID` | Current run identifier |
| `DOMINO_STARTING_USERNAME` | User who started the app |

## Inter-App Communication

Domino apps can communicate with each other using bearer token authentication. This is useful for:
- Calling Model APIs from an app
- App-to-app service calls
- Accessing internal Domino services

### Getting the Access Token

Domino provides an access token service at `localhost:8899`:

```python
import requests

# Get bearer token for inter-app communication
API_TOKEN = requests.get("http://localhost:8899/access-token").text
```

### Making Authenticated Requests

```python
import requests

# 1. Get access token from Domino's token service
API_TOKEN = requests.get("http://localhost:8899/access-token").text

# 2. Set up headers with bearer token
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# 3. Make request to another Domino app or service
payload = {
    "query": "Your request data here"
}

try:
    resp = requests.post(
        "https://your-domino-instance/apps-internal/APP_ID/endpoint",
        json=payload,
        headers=headers,
        timeout=100
    )
    resp.raise_for_status()
    data = resp.json()
    print(data)
except requests.exceptions.RequestException as err:
    print("API call failed:", err)
```

### Key Points

- **Token endpoint**: `http://localhost:8899/access-token` (only accessible from within Domino)
- **Token type**: Bearer token for Authorization header
- **Use cases**: Model API calls, app-to-app communication, internal services
- **Timeout**: Set appropriate timeouts for long-running requests

## Blueprint Reference

Official React CI/CD Blueprint:
https://github.com/dominodatalab/domino-blueprints/tree/main/React-app-deployment-with-CICD
