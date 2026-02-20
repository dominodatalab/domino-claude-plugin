---
description: Debug Domino proxy and routing issues for web applications. Analyzes vite.config.js, package.json, and app.sh for misconfigurations.
---

# /domino-debug-proxy Command

Diagnose and fix common Domino proxy and routing issues for web applications.

## Usage

```
/domino-debug-proxy
```

## What This Command Checks

### 1. Port Configuration
- Verifies port 8888 is used
- Checks for hardcoded ports in config files
- Validates strictPort settings

### 2. Base Path Configuration
- For React/Vite: Checks `base: './'` in vite.config.js
- For other frameworks: Checks relative path usage

### 3. Host Binding
- Verifies `host: '0.0.0.0'` (not localhost or 127.0.0.1)
- Checks server configuration in all frameworks

### 4. app.sh Analysis
- Checks for correct working directory
- Verifies build commands
- Validates serve configuration

### 5. Asset Loading
- Checks for hardcoded absolute paths
- Verifies relative asset references

## Common Issues Detected

### Issue: Wrong Port

**Symptom:** App shows "Connection refused"

**Detection:**
```
❌ Found port 3000 in vite.config.js
   Expected: 8888
```

**Fix:**
```javascript
server: {
  port: 8888,
  strictPort: true
}
```

### Issue: Absolute Base Path

**Symptom:** 404 errors on CSS/JS files

**Detection:**
```
❌ vite.config.js has base: '/' or no base specified
   This causes asset 404s behind Domino proxy
```

**Fix:**
```javascript
export default defineConfig({
  base: './',
  // ...
})
```

### Issue: Localhost Binding

**Symptom:** App not accessible from browser

**Detection:**
```
❌ Server bound to localhost/127.0.0.1
   Domino proxy cannot reach the app
```

**Fix:**
```javascript
server: {
  host: '0.0.0.0',
  // ...
}
```

### Issue: Missing SPA Fallback

**Symptom:** Direct URL access returns 404

**Detection:**
```
❌ app.sh uses 'npx serve dist' without -s flag
   Client-side routing will fail
```

**Fix:**
```bash
npx serve -s dist -l 8888
```

### Issue: Build Not Running

**Symptom:** Blank page or old content

**Detection:**
```
❌ app.sh missing 'npm run build' step
   App may be serving stale or no content
```

**Fix:**
```bash
#!/bin/bash
set -e
cd /mnt/code
npm ci
npm run build  # Add this line
npx serve -s dist -l 8888
```

## Output Format

```
🔍 Domino Proxy Debug Report
============================

Checking: vite.config.js
✅ Port: 8888
✅ Base path: './'
✅ Host: 0.0.0.0

Checking: app.sh
✅ Working directory: /mnt/code
✅ Build command: npm run build
❌ Serve command missing -s flag

Checking: package.json
✅ serve dependency present
✅ Build script defined

Summary:
--------
Found 1 issue(s)

Recommended fixes:
1. Update app.sh serve command:
   - Current: npx serve dist -l 8888
   + Fixed:   npx serve -s dist -l 8888
```

## Automatic Fixes

The command can automatically fix certain issues:

```
Would you like to apply automatic fixes? [Y/n]
```

Fixes that can be applied:
- Update vite.config.js base path
- Fix port configuration
- Add -s flag to serve command
- Update host binding

## Manual Investigation

For issues that can't be auto-fixed, the command provides:

1. **Browser console commands** to run for debugging
2. **Network tab guidance** for checking requests
3. **Log locations** to check in Domino

## Related Commands

- `/domino-app-init` - Initialize a new app with correct settings
- `/domino-experiment-setup` - Set up experiment tracking
- `/domino-trace-setup` - Set up GenAI tracing

## Examples

```bash
# Run debug analysis
/domino-debug-proxy

# Fix issues automatically
/domino-debug-proxy --fix
```
