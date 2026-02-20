#!/bin/bash
# Domino App Entry Point for Vite React Application
# This script is executed when the Domino App starts

set -e

echo "=== Domino Vite React App ==="
echo "Project: ${DOMINO_PROJECT_NAME:-unknown}"
echo "Owner: ${DOMINO_PROJECT_OWNER:-unknown}"
echo "User: ${DOMINO_STARTING_USERNAME:-unknown}"

# Navigate to code directory
cd /mnt/code

# Install dependencies (ci for faster, deterministic installs)
echo "Installing dependencies..."
npm ci

# Build production bundle
echo "Building production bundle..."
npm run build

# Serve the built app with SPA fallback
# -s: Single Page Application mode (serves index.html for all routes)
# -l: Listen on port 8888 (default for Domino apps)
# --no-clipboard: Don't try to copy URL to clipboard
echo "Starting server on port 8888..."
npx serve -s dist -l 8888 --no-clipboard
