#!/bin/bash
# Domino App Entry Point for Dash Application
# This script is executed when the Domino App starts

set -e

echo "=== Domino Dash App ==="
echo "Project: ${DOMINO_PROJECT_NAME:-unknown}"
echo "Owner: ${DOMINO_PROJECT_OWNER:-unknown}"
echo "User: ${DOMINO_STARTING_USERNAME:-unknown}"

# Navigate to code directory
cd /mnt/code

# Optional: Install any additional dependencies
# pip install -r requirements.txt

# Start Dash application
# The app.py file should bind to 0.0.0.0:8888
python app.py
