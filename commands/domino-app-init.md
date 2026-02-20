---
description: Initialize a new Domino-ready web application with Vite+React, Streamlit, Dash, or Flask. Configures proxy-compatible settings and app.sh.
---

# /domino-app-init Command

Initialize a Domino-ready web application with the correct configuration for Domino's reverse proxy.

## Usage

```
/domino-app-init [framework]
```

## Supported Frameworks

- `react` or `vite-react` - React application with Vite (default)
- `streamlit` - Streamlit application
- `dash` - Plotly Dash application
- `flask` - Flask application
- `gradio` - Gradio application

## What This Command Does

1. **Detects or asks for framework choice**
2. **Creates app.sh** - Entry point script for Domino
3. **Configures port binding** - Uses port 8888 by default (flexible)
4. **Sets up proxy-compatible settings** - For React: `base: './'`
5. **Creates .env.example** - Template for environment variables
6. **Adds Model API integration** - Code for calling model endpoints

## React/Vite Output

### vite.config.js
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  server: { host: '0.0.0.0', port: 8888, strictPort: true },
  preview: { host: '0.0.0.0', port: 8888, strictPort: true },
  build: { outDir: 'dist', assetsDir: 'assets' }
})
```

### app.sh
```bash
#!/bin/bash
set -e
cd /mnt/code
npm ci
npm run build
npx serve -s dist -l 8888 --no-clipboard
```

### .env.example
```
VITE_MODEL_API_URL=https://your-domino.com/models/MODEL_ID/latest/model
VITE_MODEL_API_TOKEN=your_api_token
```

## Streamlit Output

### app.sh
```bash
#!/bin/bash
set -e
streamlit run app.py \
    --server.port 8888 \
    --server.address 0.0.0.0 \
    --server.headless true
```

## Dash Output

### app.py (with Domino configuration)
```python
import os
from dash import Dash, html

app = Dash(__name__)
app.layout = html.Div([html.H1("Domino Dash App")])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8888, debug=False)
```

### app.sh
```bash
#!/bin/bash
set -e
python app.py
```

## Flask Output

### app.py (with Domino configuration)
```python
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Domino Flask App"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)
```

### app.sh
```bash
#!/bin/bash
set -e
python app.py
```

## Interactive Mode

When run without arguments, the command will prompt for:

1. **Framework selection** - Which framework to use
2. **Project name** - Name for the project/app
3. **Include Model API** - Whether to include model API integration code
4. **Model API URL** - If including, the endpoint URL to use

## Examples

```bash
# Initialize React app
/domino-app-init react

# Initialize Streamlit app
/domino-app-init streamlit

# Interactive mode
/domino-app-init
```

## Post-Initialization Steps

After running this command:

1. **Configure environment variables** in Domino project settings
2. **Set app.sh as the app entry point** when publishing the app
3. **Test locally** using `./app.sh` before deploying
4. **Verify port 8888** is being used correctly
