---
name: domino-extensions
description: Build and operate Domino UI Extensions (mount Domino Apps in the shell with page context). Covers extension_manifest.json, official installer vs manual Extension API, publish and identity requirements, auth and host splits, and beta REST routes. Use when creating an Extension, wiring mount points, publishing an Extension App from a project, or automating Extension install lifecycle. Not for generic App deployment alone (see domino-apps) or SPA scaffolding (see domino-ui-bootstrap).
---

# Domino Extensions

An **Extension** surfaces a published **App** at a Domino UI **mount point** (project sidebar, dataset page, model details, file context menus, admin panel). Domino opens the App in a new tab and passes page context as query parameters. The App must support **extended identity propagation** so it can act as the viewing user with consent.

## When to use other skills

| Goal | Skill |
|------|--------|
| Vite/React design system, `@dominodatalab/extensions-tools`, proxy-safe URLs | [domino-ui-bootstrap](../domino-ui-bootstrap/SKILL.md) |
| `app.sh`, ports, SPA base path, generic App CI | [domino-apps](../apps/SKILL.md) |
| REST auth, jobs, projects, platform `/api/*` and `/v4/*` | [python-sdk](../python-sdk/SKILL.md) |
| Governance from an extension backend | [domino-governance](../domino-governance/SKILL.md) plus external URL rules below |

Product overview: https://docs.domino.ai/cloud/platform-capabilities/features/extensions

Official catalog install (SysAdmin/CloudAdmin): https://docs.domino.ai/cloud/platform-capabilities/features/extensions/install-domino-official-extensions

Authentication: https://docs.domino.ai/cloud/reference/api/domino-api-authentication . For HTTP client setup in Extension backends and install scripts, use [python-sdk/SKILL.md](../python-sdk/SKILL.md#authentication).

## Extension manifest (`extension_manifest.json`)

Domino Official Extensions and custom Extension repos ship a manifest at the repo root. Schema version is **`manifestSchemaVersion`: 1** (integer). The official installer reads this file from a GitHub release; manual flows still mirror the same shape when you create entities yourself.

Top-level sections:

| Section | Purpose |
|---------|---------|
| `project` | Hosting project (`name`, `description`, `visibility`, `isRestricted`, ...) |
| `app` | Compute environment, entry point, vanity URL, visibility, mounts, hardware tier |
| `extension` | Extension record: `name`, `description`, `enabled`, `uiMountPointTypeConfigs` |

For full manifest examples and patterns (compute environment, mount configs, deep linking, autoscaling), refer to Domino's official Extension repos:

- https://github.com/dominodatalab/AutoML_Extension
- https://github.com/dominodatalab/clinical-data-explorer
- https://github.com/dominodatalab/AutoDocumentation_Extension

Each ships an `extension_manifest.json` at the repo root; read the file matching your Domino version rather than copying from this skill.

### Mount points (`uiMountPointTypeConfigs`)

Keys match the Extensions API enum: `projectSidebar`, `dataset`, `datasetFileContext`, `modelDetails`, `adminPanel`, `netAppVolume`, `netAppVolumeFileContext`. Each mount defines `enabled`, scope (for example `allProjects` or project lists), and `urlConfig` with `contextualQueryParams` Domino passes to the App.

Domino documents five primary user-facing mount types on the product page; the API includes NetApp-related mount types for volume integrations.

### Deep linking vs iframe (`renderIFrame`)

Apps can run full-page (deep linking) or inside an iframe. Platform convention: **`renderIFrame = !deepLinkingEnabled`**. Manifest field **`enableDeepLinking: true`** means the App expects full-page navigation; set `false` when the UI should load in an iframe. Align manifest, App publish settings, and start overrides so you do not mix modes silently.

## Publish from a project (custom Extension)

Typical human workflow:

1. **Build the App** in a project (frontend plus optional backend). Enable extended identity propagation; Flask/Dash read proxied headers by default.
2. **Publish the App** as a SysAdmin or CloudAdmin (App must be published before it backs an Extension). Use the Apps API publish chain (`/api/apps/v1/...` and related routes). See [python-sdk/API-APPS.md](../python-sdk/API-APPS.md) and https://docs.domino.ai/cloud/reference/api/domino-open-api (Apps tags).
3. **Create the Extension** via Admin UI or **`POST /api/extensions/beta/extensions`** with `appId`, optional `appVersionId`, `name`, `enabled`, and `uiMountPointTypeConfigs`.

REST surface (beta): prefix **`/api/extensions/beta/`** (`extensions`, `extensions-ui`, `official-installs`, ...). Confirm operation IDs and bodies in deployment `public-api.json` or https://docs.domino.ai/llms-full.txt .

```python
import os
import requests

if os.environ.get("DOMINO_API_PROXY"):
    base_url = os.environ["DOMINO_API_PROXY"].rstrip("/")
    headers = {}
else:
    base_url = (os.environ.get("DOMINO_USER_HOST") or os.environ.get("DOMINO_API_HOST") or "").rstrip("/")
    token = requests.get("http://localhost:8899/access-token").text.strip()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

body = {
    "name": "My Extension",
    "enabled": True,
    "appId": "app-id-from-publish",
    "uiMountPointTypeConfigs": {
        "projectSidebar": {
            "enabled": True,
            "allProjects": True,
            "urlConfig": {"contextualQueryParams": ["projectId"]},
        }
    },
}
response = requests.post(f"{base_url}/api/extensions/beta/extensions", headers=headers, json=body)
```

Only Admins create Extensions; viewers grant consent when the App acts as them.

### Official Extension install (manifest-driven)

For Domino-built Extensions, an admin installs from **Manage Domino-official Extensions** in the Admin panel. The installer creates project, environment, App, and Extension from the release manifest (background job with retry/cancel). API analogs: `official-install-menu`, `POST .../official-installs`, snapshot status endpoints under `/api/extensions/beta/official-installs/`.

Do not edit installer-managed project, environment, App, or Extension by hand; use the official install UI for version changes.

## Auth, identity, and hosts in Extension Apps

| Context | Guidance |
|---------|----------|
| **App backend** calling platform APIs as the **starting user** | `DOMINO_API_PROXY` if set (no Authorization header); else access-token plus platform host. See [python-sdk](../python-sdk/SKILL.md). |
| **Visitor identity** in the browser | Visitor JWT from the App ingress; validate with JWKS. **`GET /v4/users/self` with a visitor JWT often fails** for privileged data; do not assume it replaces admin APIs for org/role lists. |
| **Governance** `/api/governance/v1/*` | On many deployments the run sidecar does **not** route governance; use **public deployment URL** plus PAT/SA Bearer, not sidecar plus API key. |
| **Inference** `/endpoints/{vanity}` | Use the **`url`** from the GenAI/management API response, not `DOMINO_USER_HOST`. |
| **Automation outside any run** | Public deployment URL plus PAT or SA only. |

Domino does not inject a single `DOMINO_EXTERNAL_URL`; derive public URL from deployment config, forwarded headers, or app conventions (`DOMINO_PUBLIC_HOST` / `DOMINO_EXTERNAL_HOST` are app patterns, not guaranteed core run injection).

## Platform caveats (Apps API + Extensions)

These affect Extension Apps the same as standalone Apps:

| Topic | Behavior |
|-------|----------|
| **`netAppVolumeIds` on App version create** | Accepted in the API but NetApp volumes may **not mount** (silent no-op vs workspace parity). Prefer explicit volume workflows; manifest `mountNetAppVolumes` does not fix API no-op alone. |
| **App delete and vanity URL** | Deleting an App may **not release** its vanity URL for immediate reuse; recreate failures may need admin cleanup. |
| **Apps beta vs v1** | Extension backing Apps may be created or published through beta or v1 routes; check `public-api.json` for your deployment. Prefer documented v1 publish flows for new automation where available. |

## Prerequisites on the deployment

- Extensions feature enabled.
- **`SecureIdentityPropagationToAppsEnabled`** and extended identity propagation for Apps (default on Domino Cloud).
- For official installs: platform egress to GitHub for catalog, manifests, and release artifacts.

## Related API reference

- Extensions tag in Platform API: https://docs.domino.ai/cloud/reference/api/domino-open-api
- Apps tag (publish chain): [python-sdk/API-APPS.md](../python-sdk/API-APPS.md)
