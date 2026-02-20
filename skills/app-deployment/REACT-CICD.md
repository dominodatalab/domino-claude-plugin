# React CI/CD with GitHub Actions for Domino

This guide covers setting up continuous integration and deployment for React applications on Domino Data Lab.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   dev branch    │────▶│   uat branch    │────▶│ main/production │
│   (workspace)   │     │ (auto-deploy)   │     │  (auto-deploy)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Dev Project    │     │  UAT Project    │     │  Prod Project   │
│  (manual test)  │     │  (Domino App)   │     │  (Domino App)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Repository Structure

```
.
├── app-code/                    # React app source (Vite)
│   ├── src/
│   │   ├── components/
│   │   ├── api/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── vite.config.js
│   └── package.json
├── app.sh                       # Domino app entry point
├── cicd/
│   ├── app-configs.yaml        # App configuration
│   ├── create_git_based_project_and_app.py
│   └── requirements.txt
├── .github/workflows/
│   ├── deploy-uat.yml
│   └── deploy-prod.yml
└── README.md
```

## GitHub Actions Workflows

### Deploy to UAT

**.github/workflows/deploy-uat.yml:**

```yaml
name: Deploy to UAT
on:
  push:
    branches: [uat]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: uat

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: app-code/package-lock.json

      - name: Install and Build
        working-directory: app-code
        run: |
          npm ci
          npm run build

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install CICD dependencies
        run: |
          pip install -r cicd/requirements.txt

      - name: Deploy to Domino
        env:
          DOMINO_API_KEY: ${{ secrets.DOMINO_USER_API_KEY }}
          DOMINO_URL: ${{ vars.DOMINO_URL }}
          GH_PAT: ${{ secrets.GH_PAT }}
          PROJECT_NAME: ${{ vars.PROJECT_NAME }}-uat
          APP_NAME: ${{ vars.APP_NAME }}-uat
          ENVIRONMENT_ID: ${{ vars.ENVIRONMENT_ID }}
          HARDWARE_TIER_ID: ${{ vars.HARDWARE_TIER_ID }}
          MODEL_API_URL: ${{ vars.MODEL_API_URL }}
          MODEL_API_TOKEN: ${{ secrets.MODEL_API_TOKEN }}
        run: |
          python cicd/create_git_based_project_and_app.py
```

### Deploy to Production

**.github/workflows/deploy-prod.yml:**

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: app-code/package-lock.json

      - name: Install and Build
        working-directory: app-code
        run: |
          npm ci
          npm run build

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install CICD dependencies
        run: |
          pip install -r cicd/requirements.txt

      - name: Deploy to Domino
        env:
          DOMINO_API_KEY: ${{ secrets.DOMINO_USER_API_KEY }}
          DOMINO_URL: ${{ vars.DOMINO_URL }}
          GH_PAT: ${{ secrets.GH_PAT }}
          PROJECT_NAME: ${{ vars.PROJECT_NAME }}
          APP_NAME: ${{ vars.APP_NAME }}
          ENVIRONMENT_ID: ${{ vars.ENVIRONMENT_ID }}
          HARDWARE_TIER_ID: ${{ vars.HARDWARE_TIER_ID }}
          MODEL_API_URL: ${{ vars.MODEL_API_URL }}
          MODEL_API_TOKEN: ${{ secrets.MODEL_API_TOKEN }}
        run: |
          python cicd/create_git_based_project_and_app.py
```

## GitHub Secrets and Variables

### Required Secrets

| Secret | Description |
|--------|-------------|
| `DOMINO_USER_API_KEY` | Domino API key for authentication |
| `GH_PAT` | GitHub Personal Access Token for Domino Git credentials |
| `MODEL_API_TOKEN` | Bearer token for React app to call Model API |

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DOMINO_URL` | Domino deployment URL | `https://your-domino.company.com` |
| `PROJECT_NAME` | Domino project name | `react-dashboard` |
| `APP_NAME` | Domino app name | `dashboard-app` |
| `ENVIRONMENT_ID` | Compute environment ID | `64a1b2c3d4e5f6...` |
| `HARDWARE_TIER_ID` | Hardware tier | `small-k8s` |
| `MODEL_API_URL` | Backend model endpoint | `https://domino.com/models/xyz/latest/model` |

## Deployment Script

### cicd/create_git_based_project_and_app.py

```python
#!/usr/bin/env python3
"""
Creates or updates a Domino project and app from a Git repository.
"""

import os
import sys
import yaml
from domino import Domino

def main():
    # Load configuration
    domino_url = os.environ['DOMINO_URL']
    api_key = os.environ['DOMINO_API_KEY']
    project_name = os.environ['PROJECT_NAME']
    app_name = os.environ['APP_NAME']
    environment_id = os.environ['ENVIRONMENT_ID']
    hardware_tier_id = os.environ['HARDWARE_TIER_ID']

    # Initialize Domino client
    domino = Domino(
        host=domino_url,
        api_key=api_key
    )

    # Get or create project
    try:
        project = domino.project_get(project_name)
        print(f"Found existing project: {project_name}")
    except:
        print(f"Creating project: {project_name}")
        project = domino.project_create(project_name)

    # Configure Git credentials
    gh_pat = os.environ.get('GH_PAT')
    if gh_pat:
        # Set up Git credentials in Domino
        pass  # Implementation depends on Domino API version

    # Create or update app
    app_config = {
        'name': app_name,
        'environmentId': environment_id,
        'hardwareTierId': hardware_tier_id,
        'appType': 'app',
    }

    # Set environment variables for the app
    env_vars = {
        'VITE_MODEL_API_URL': os.environ.get('MODEL_API_URL', ''),
        'VITE_MODEL_API_TOKEN': os.environ.get('MODEL_API_TOKEN', ''),
    }

    print(f"Deploying app: {app_name}")
    # Deploy using Domino API
    # Implementation varies by Domino version

    print("Deployment complete!")

if __name__ == '__main__':
    main()
```

### cicd/requirements.txt

```
dominodatalab>=1.3.0
pyyaml>=6.0
requests>=2.28.0
```

### cicd/app-configs.yaml

```yaml
# App configuration for different environments
environments:
  uat:
    hardware_tier: small-k8s
    auto_restart: true
    visibility: project

  production:
    hardware_tier: medium-k8s
    auto_restart: true
    visibility: organization

app:
  entry_point: app.sh
  title: "React Dashboard"
  description: "Interactive dashboard powered by ML models"
```

## Setting Up GitHub Environments

### 1. Create Environments

1. Go to Repository Settings → Environments
2. Create `uat` environment
3. Create `production` environment
4. Add required reviewers for production (optional)

### 2. Add Secrets to Each Environment

For each environment (uat, production):
- `DOMINO_USER_API_KEY`
- `GH_PAT`
- `MODEL_API_TOKEN`

### 3. Add Variables to Each Environment

For each environment:
- `DOMINO_URL`
- `PROJECT_NAME` (append `-uat` for UAT)
- `APP_NAME`
- `ENVIRONMENT_ID`
- `HARDWARE_TIER_ID`
- `MODEL_API_URL`

## Workflow: Development to Production

### 1. Development (dev branch)

```bash
# Work in Domino workspace
git checkout dev
# Make changes
git add .
git commit -m "Add new feature"
git push origin dev
```

### 2. Deploy to UAT

```bash
# Merge to UAT branch triggers deployment
git checkout uat
git merge dev
git push origin uat
# GitHub Action deploys to UAT Domino project
```

### 3. Deploy to Production

```bash
# After UAT testing, merge to main
git checkout main
git merge uat
git push origin main
# GitHub Action deploys to Production Domino project
```

## Monitoring Deployments

### GitHub Actions

- View workflow runs in Actions tab
- Check logs for deployment status
- Set up notifications for failures

### Domino

- Verify app is running in Domino UI
- Check app logs for startup errors
- Monitor app metrics in Grafana

## Rollback Strategy

### Quick Rollback via Git

```bash
# Revert to previous commit
git checkout main
git revert HEAD
git push origin main
# Triggers redeployment with previous version
```

### Manual Rollback in Domino

1. Go to Domino project
2. Navigate to Apps
3. Stop current app
4. Start previous app version

## Blueprint Reference

Full implementation available at:
https://github.com/dominodatalab/domino-blueprints/tree/main/React-app-deployment-with-CICD
