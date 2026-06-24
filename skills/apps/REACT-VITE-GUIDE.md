# React + Vite Deployment Guide for Domino

This guide covers deploying React applications built with Vite to Domino Data Lab.

## Understanding Domino's Proxy Architecture

```
User Request: https://domino.company.com/jsmith/myproject/app/dashboard/settings

Domino Proxy Layer:
├── Authenticates user
├── Strips prefix: /jsmith/myproject/app/dashboard/
├── Forwards to container port 8888
└── Injects headers: X-Domino-User, X-Domino-Project

Your App Container:
└── Receives request at port 8888, path: /settings
```

### Why React Apps Break Without Proper Configuration

1. React builds assume assets are served from root `/`
2. Browser requests `/static/js/main.js` → 404 error
3. Should request `/owner/project/app/name/static/js/main.js`

**Solution**: Use relative paths with `base: './'` in Vite config.

## Vite Configuration

### vite.config.js (Production-Ready)

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  // CRITICAL: Use relative base path for Domino proxy
  base: './',

  server: {
    host: '0.0.0.0',
    port: 8888,
    strictPort: true,
  },

  preview: {
    host: '0.0.0.0',
    port: 8888,
    strictPort: true,
  },

  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  }
})
```

### Key Configuration Options Explained

| Option | Value | Purpose |
|--------|-------|---------|
| `base` | `'./'` | Makes all asset paths relative |
| `server.host` | `'0.0.0.0'` | Binds to all interfaces |
| `server.port` | `8888` | Domino's expected port |
| `strictPort` | `true` | Fails if port unavailable |

## app.sh Production Script

```bash
#!/bin/bash
set -e

echo "=== Domino Vite React App ==="
echo "Project: $DOMINO_PROJECT_NAME"
echo "Owner: $DOMINO_PROJECT_OWNER"

cd /mnt/code

# Install dependencies
npm ci

# Build production bundle
npm run build

# Serve with SPA fallback using 'serve' package
npx serve -s dist -l 8888 --no-clipboard
```

### Why `serve -s`?

The `-s` flag enables single-page application mode:
- Serves `index.html` for all routes that don't match a file
- Required for client-side routing (React Router)

## Connecting to Model API Endpoints

### Environment Variables Setup

Create a `.env` file for local development:

```bash
# .env.local
VITE_MODEL_API_URL=https://your-domino.com/models/abc123/latest/model
VITE_MODEL_API_TOKEN=your_api_token_here
```

### API Client Implementation

```javascript
// src/api/modelApi.js
const MODEL_API_URL = import.meta.env.VITE_MODEL_API_URL;
const MODEL_API_TOKEN = import.meta.env.VITE_MODEL_API_TOKEN;

export async function predict(inputData) {
  const response = await fetch(MODEL_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${MODEL_API_TOKEN}`,
    },
    body: JSON.stringify({ data: inputData }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

### Using in React Components

```javascript
// src/App.jsx
import { useState } from 'react';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const callAPI = async (inputData) => {
    setLoading(true);
    try {
      const modelApiUrl = import.meta.env.VITE_MODEL_API_URL;
      const modelApiToken = import.meta.env.VITE_MODEL_API_TOKEN;

      const response = await fetch(modelApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${modelApiToken}`,
        },
        body: JSON.stringify(inputData),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('API call failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={() => callAPI({ feature1: 1.0, feature2: 2.0 })}>
        Get Prediction
      </button>
      {loading && <p>Loading...</p>}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}

export default App;
```

## Development in Domino Workspace

### Preview Setup Script

```bash
#!/bin/bash
# setup_app_preview.sh

cd /mnt/code

# Install dependencies
npm install

# Start dev server
npm run dev -- --host 0.0.0.0 --port 8888
```

### Accessing Development Preview

Preview URL pattern in Domino workspace:
```
https://<domino-url>/<owner>/<project>/notebookSession/<run-id>/proxy/8888/
```

## Client-Side Routing (React Router)

### Configuration for Domino

```javascript
// src/main.jsx
import { BrowserRouter } from 'react-router-dom';

// Use basename for proper routing behind proxy
const basename = window.location.pathname.replace(/\/[^/]*$/, '');

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter basename={basename}>
    <App />
  </BrowserRouter>
);
```

### Alternative: Hash Router

For simpler setup without basename complexity:

```javascript
import { HashRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')).render(
  <HashRouter>
    <App />
  </HashRouter>
);
```

URLs will be: `https://domino.company.com/owner/project/app/name/#/dashboard`

## Common Pitfalls

### 1. Hardcoded API URLs

**Wrong:**
```javascript
fetch('http://localhost:3000/api/predict')
```

**Correct:**
```javascript
fetch(import.meta.env.VITE_MODEL_API_URL)
```

### 2. Missing base Configuration

**Wrong:**
```javascript
export default defineConfig({
  plugins: [react()],
  // No base specified - defaults to '/'
})
```

**Correct:**
```javascript
export default defineConfig({
  plugins: [react()],
  base: './',  // Relative paths
})
```

### 3. Wrong Port

**Wrong:**
```javascript
server: { port: 3000 }
```

**Correct:**
```javascript
server: { port: 8888, strictPort: true }
```

## Complete Project Structure

```
my-react-app/
├── src/
│   ├── api/
│   │   └── modelApi.js
│   ├── components/
│   ├── App.jsx
│   └── main.jsx
├── public/
├── vite.config.js
├── package.json
├── app.sh
├── .env.example
└── .gitignore
```
