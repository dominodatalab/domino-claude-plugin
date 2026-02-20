# Troubleshooting Domino App Deployment

This guide covers common issues and solutions when deploying web applications to Domino Data Lab.

## Common Issues

### 1. 404 Errors on Asset Loading

**Symptoms:**
- Page loads but CSS/JS files return 404
- Console shows requests to wrong paths
- Styles missing, JavaScript not executing

**Cause:** React/Vite building with absolute paths instead of relative.

**Solution:**

```javascript
// vite.config.js
export default defineConfig({
  base: './',  // CRITICAL - use relative paths
  // ...
})
```

**Verification:**
```bash
# After build, check index.html
cat dist/index.html | grep -o 'src="[^"]*"'
# Should show: src="./assets/..." NOT src="/assets/..."
```

### 2. Blank Page After Deployment

**Symptoms:**
- App loads in development but shows blank page in production
- No errors in browser console
- Network tab shows successful requests

**Possible Causes:**

1. **JavaScript errors** - Check browser console
2. **Wrong entry point** - Verify app.sh path
3. **Missing build step** - Ensure `npm run build` runs

**Debug Steps:**

```bash
# Check app.sh is executable
ls -la app.sh

# Verify build output exists
ls -la dist/

# Check index.html content
head -20 dist/index.html
```

### 3. App Not Accessible (Connection Refused)

**Symptoms:**
- App status shows "Running" in Domino
- Clicking app URL shows connection error
- Logs show app started successfully

**Cause:** App not binding to correct host/port.

**Solution:**

```javascript
// vite.config.js - Development
server: {
  host: '0.0.0.0',  // NOT 'localhost' or '127.0.0.1'
  port: 8888,       // Must be 8888
  strictPort: true
}
```

```bash
# app.sh - Production
npx serve -s dist -l 8888  # Port 8888
```

**For other frameworks:**
```python
# Flask
app.run(host='0.0.0.0', port=8888)

# Streamlit
# streamlit run app.py --server.port 8888 --server.address 0.0.0.0
```

### 4. Client-Side Routing Broken (React Router)

**Symptoms:**
- Homepage works
- Direct navigation to routes (e.g., `/dashboard`) returns 404
- Refresh on non-root routes fails

**Cause:** Server doesn't know about client-side routes.

**Solution 1: Use serve with SPA mode**

```bash
# app.sh
npx serve -s dist -l 8888  # -s flag enables SPA fallback
```

**Solution 2: Use HashRouter**

```javascript
// main.jsx
import { HashRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')).render(
  <HashRouter>
    <App />
  </HashRouter>
);
```

**Solution 3: Configure basename**

```javascript
// main.jsx
const basename = window.location.pathname.replace(/\/[^/]*$/, '');

<BrowserRouter basename={basename}>
  <App />
</BrowserRouter>
```

### 5. API Calls Failing (CORS or Auth)

**Symptoms:**
- App loads but API calls fail
- Console shows CORS errors
- 401/403 responses from API

**Debugging:**

```javascript
// Add detailed error logging
const callAPI = async (data) => {
  console.log('API URL:', import.meta.env.VITE_MODEL_API_URL);
  console.log('Token exists:', !!import.meta.env.VITE_MODEL_API_TOKEN);

  try {
    const response = await fetch(import.meta.env.VITE_MODEL_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${import.meta.env.VITE_MODEL_API_TOKEN}`,
      },
      body: JSON.stringify(data),
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', [...response.headers.entries()]);

    return response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

**Common Fixes:**

1. **Missing environment variables** - Check `.env` file and Domino app settings
2. **Wrong token format** - Ensure `Bearer ` prefix
3. **CORS** - Model endpoint must allow cross-origin requests

### 6. Environment Variables Not Available

**Symptoms:**
- `import.meta.env.VITE_*` returns `undefined`
- App works locally but not in Domino

**Cause:** Vite environment variables must be prefixed with `VITE_`.

**Solution:**

```bash
# .env or Domino app environment
VITE_MODEL_API_URL=https://...  # VITE_ prefix required
VITE_MODEL_API_TOKEN=token123
```

**For runtime variables (not baked into build):**

```javascript
// Use window.ENV for runtime config
// Create a config endpoint or inject at runtime
```

### 7. App Crashes on Startup

**Symptoms:**
- App status shows "Error" or keeps restarting
- Logs show immediate crash

**Debug Steps:**

```bash
# Check app.sh syntax
bash -n app.sh

# Test locally
chmod +x app.sh
./app.sh
```

**Common Issues:**

1. **Missing dependencies**
```bash
# app.sh - ensure npm ci runs
npm ci  # Not npm install
```

2. **Wrong working directory**
```bash
# app.sh - verify path
cd /mnt/code  # Standard Domino path
ls -la        # Verify files exist
```

3. **Permission errors**
```bash
# Make app.sh executable in repo
git update-index --chmod=+x app.sh
```

### 8. Slow App Startup

**Symptoms:**
- App takes minutes to become available
- Timeout errors during deployment

**Causes and Solutions:**

1. **Large npm install**
```bash
# Use npm ci for faster, deterministic installs
npm ci  # NOT npm install
```

2. **Build included in startup**
```bash
# Pre-build in CI/CD instead of app.sh
# Or use Domino Docker build
```

3. **Downloading models at startup**
```python
# Cache models in environment or artifacts
# Don't download on every app start
```

### 9. WebSocket Connection Issues

**Symptoms:**
- Streamlit shows connection errors
- Real-time features not working
- Intermittent disconnections

**Solution for Streamlit:**

```bash
# app.sh
streamlit run app.py \
    --server.port 8888 \
    --server.address 0.0.0.0 \
    --server.enableCORS false \
    --server.enableXsrfProtection false
```

## Diagnostic Tools

### Check App Logs

```bash
# In Domino UI
# Go to Project > Apps > Select App > Logs

# Or via API
curl -H "X-Domino-Api-Key: $API_KEY" \
  "$DOMINO_URL/v4/apps/$APP_ID/logs"
```

### Test Port Binding Locally

```bash
# Test if port 8888 is available
lsof -i :8888

# Test app binding
curl -v http://localhost:8888
```

### Verify Build Output

```bash
# Check build creates expected files
npm run build
ls -la dist/
cat dist/index.html | head -30

# Verify asset paths are relative
grep -r 'src="\/' dist/  # Should return nothing
grep -r 'href="\/' dist/ # Should return nothing
```

### Test in Docker Locally

```dockerfile
# Test Dockerfile
FROM node:18

WORKDIR /mnt/code
COPY . .

RUN npm ci
RUN npm run build

EXPOSE 8888
CMD ["npx", "serve", "-s", "dist", "-l", "8888"]
```

```bash
docker build -t test-app .
docker run -p 8888:8888 test-app
# Visit http://localhost:8888
```

## Quick Reference: Common Fixes

| Issue | Quick Fix |
|-------|-----------|
| 404 on assets | `base: './'` in vite.config.js |
| Connection refused | `host: '0.0.0.0'` and `port: 8888` |
| Blank page | Check browser console for JS errors |
| Routing broken | Use `serve -s` or HashRouter |
| Env vars undefined | Prefix with `VITE_` |
| Slow startup | Use `npm ci` instead of `npm install` |
| API calls fail | Check CORS and auth headers |

## Getting Help

1. Check Domino app logs first
2. Test locally with same configuration
3. Review Domino documentation: https://docs.dominodatalab.com/en/latest/user_guide/e3ec27/apps-in-domino/
4. Check blueprint examples: https://github.com/dominodatalab/domino-blueprints
