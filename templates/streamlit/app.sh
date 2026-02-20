#!/bin/bash
# Domino App Entry Point for Streamlit Application
# This script is executed when the Domino App starts

set -e

echo "=== Domino Streamlit App ==="
echo "Project: ${DOMINO_PROJECT_NAME:-unknown}"
echo "Owner: ${DOMINO_PROJECT_OWNER:-unknown}"
echo "User: ${DOMINO_STARTING_USERNAME:-unknown}"

# Navigate to code directory
cd /mnt/code

# Optional: Install any additional dependencies
# pip install -r requirements.txt

# Start Streamlit server
# --server.port 8888: Default port for Domino apps (flexible)
# --server.address 0.0.0.0: Bind to all interfaces
# --server.headless true: Don't open browser automatically
# --browser.gatherUsageStats false: Disable telemetry
streamlit run app.py \
    --server.port 8888 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
