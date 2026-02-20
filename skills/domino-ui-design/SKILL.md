---
name: domino-ui-design
description: Build Domino-styled web applications matching the Domino Design System. Use when creating or styling Domino apps (Dash, Streamlit, Flask, FastAPI+HTML), generating UI components, reviewing UX, or when the user mentions "Domino app", "Domino UI", "Domino dashboard", or "Domino design system". Covers the full stack — FastAPI backend, Ant Design 5.x frontend via CDN, Domino theme tokens (colors, typography, spacing), chart styling with Highcharts, Domino API authentication, proxy-safe routing, UX writing, error handling, empty states, form design, table patterns, and layout best practices. Also use for UX reviews of existing Domino app screenshots.
---

# Domino UI Design System Skill

## Architecture

Domino apps use **FastAPI** (Python backend) + **Ant Design 5.x** (frontend via CDN, no build step). Avoid inline styles and JS — use statically referenced CSS/JS files. Output errors to stdout.

### CDN Setup

Include in HTML `<head>`:

```html
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/antd@5.11.2/dist/antd.min.js"></script>
<link href="https://unpkg.com/antd@5.11.2/dist/reset.css" rel="stylesheet">
<script src="https://unpkg.com/dayjs@1.11.10/dayjs.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://code.highcharts.com/highcharts.js"></script>
```

Use `React.createElement()` (aliased as `h`) — no JSX, no build step:

```javascript
const { ConfigProvider, Button, Table, Modal, Select, Input, Form, Space, Card, Tag, Alert } = antd;
const { createElement: h, useState, useEffect } = React;
```

## Domino Theme

Wrap the app in `ConfigProvider` with this theme:

```javascript
const dominoTheme = {
  token: {
    colorPrimary: '#543FDE',          // Purple
    colorPrimaryHover: '#3B23D1',
    colorPrimaryActive: '#311EAE',
    colorText: '#2E2E38',
    colorTextSecondary: '#65657B',
    colorTextTertiary: '#8F8FA3',
    colorSuccess: '#28A464',
    colorWarning: '#CCB718',
    colorError: '#C20A29',
    colorInfo: '#0070CC',
    colorBgContainer: '#FFFFFF',
    colorBgLayout: '#FAFAFA',
    colorBorder: '#E0E0E0',
    fontFamily: 'Inter, Lato, Helvetica Neue, Helvetica, Arial, sans-serif',
    fontSize: 14,
    borderRadius: 4,
    borderRadiusLG: 8,
  },
  components: {
    Button: { primaryShadow: 'none', defaultShadow: 'none' },
    Table: { headerBg: '#FAFAFA', rowHoverBg: '#F5F5F5' },
  },
};
```

### Top Navigation Bar

Height: 44px, Background: `#2E2E38`, Text: `#FFFFFF`. Use the Domino logo (height 32px). Primary actions on right. Only add nav items with real destinations.

**Domino Logo:** Reference `assets/domino-logo.svg` from this skill's directory (e.g. `.claude/skills/domino-ui-design/assets/domino-logo.svg`). The SVG is white text on transparent background, designed for the dark nav bar.

### Charts (Highcharts)

```javascript
Highcharts.setOptions({
  colors: ['#543FDE', '#0070CC', '#28A464', '#CCB718', '#FF6543', '#E835A7', '#2EDCC4', '#A9734C'],
  chart: { style: { fontFamily: 'Inter, Lato, Helvetica Neue, Arial, sans-serif' } },
});
```

## Domino API Integration

### Authentication

Re-acquire the access token on **every** API call (it expires quickly):

```python
import requests, os

def get_auth_headers():
    api_key = os.environ.get('API_KEY_OVERRIDE')
    if api_key:
        return {'X-Domino-Api-Key': api_key}
    response = requests.get('http://localhost:8899/access-token')
    token = response.text.strip()
    if token.startswith('Bearer '):
        return {'Authorization': token}
    return {'Authorization': f'Bearer {token}'}
```

### API Base Paths

Two separate APIs with **different** base paths:

| API | Base Path | Example |
|-----|-----------|---------|
| Platform APIs (swagger.json) | `/v4/` | `{DOMINO_API_HOST}/v4/jobs?projectId=...` |
| Governance APIs (governance_swagger.json) | `/api/governance/v1/` | `{DOMINO_API_HOST}/api/governance/v1/bundles?project_id=...` |

**Do NOT** add `/api/` prefix to v4 platform endpoints.

### Environment Variables (available in Domino)

`DOMINO_API_HOST`, `DOMINO_PROJECT_ID`, `DOMINO_PROJECT_NAME`, `DOMINO_PROJECT_OWNER`

Do not add mock/fake data if the API isn't working. Prompt user to set env vars.

## Running the App

Use relative URLs (not absolute) — Domino's nginx proxy modifies the root URL.

```bash
#!/bin/bash
uvicorn app:app --host 0.0.0.0 --port 8888
```

## UX Design Rules

For detailed UX principles, writing guidelines, component patterns, and review checklists, read [references/ux-design-rules.md](references/ux-design-rules.md).

Key rules to always follow:
- **Empty states must be actionable** — answer: What is this? Why is it empty? What can I do?
- **Error messages must be human-readable** with guidance on what to do next
- **Disabled elements must explain why** they're disabled (tooltip)
- **Truncated table text must have tooltips**
- **Icon-only buttons must have tooltips**
- **Use sentence case** for UI text (not Title Case)
- **No exclamation points** in UI copy
- **Side panels should overlay**, not push/crush main content
- **Checkboxes should use positive framing** — checked = ON/enabled, never checked = OFF/disabled

## UX Review

When reviewing a Domino app UI, read [references/ux-design-rules.md](references/ux-design-rules.md) and check against the review checklists. Classify issues as High/Medium/Low severity.
