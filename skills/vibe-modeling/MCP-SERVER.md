# Domino MCP Server Guide

The Domino MCP Server is a Model Context Protocol implementation that bridges AI coding assistants with the Domino Data Lab platform.

## Overview

The MCP server enables "vibe modeling" where each AI iteration is automatically tracked and reproducible in Domino. It addresses governance challenges by ensuring all AI-assisted work runs within the secure Domino environment.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  AI Assistant   │────▶│  Domino MCP      │────▶│  Domino         │
│  (Cursor, etc.) │     │  Server          │     │  Platform       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
   User prompts          REST API calls          Domino Jobs
   and context           with auth               (tracked, versioned)
```

## Available Tools

### 1. run_domino_job

Execute commands as Domino jobs within a project.

**Usage:**
```
Run a Python script in Domino: python train_model.py
```

**What happens:**
1. MCP server receives the command
2. Creates a Domino job via REST API
3. Returns job ID for status checking

### 2. check_job_status

Retrieve the execution status of a specific job run.

**Status values:**
- `Queued` - Job waiting to start
- `Running` - Job currently executing
- `Succeeded` - Job completed successfully
- `Failed` - Job encountered an error
- `Stopped` - Job was manually stopped

### 3. check_job_results

Obtain detailed results and outputs from completed jobs.

**Returns:**
- Standard output (stdout)
- Standard error (stderr)
- Artifacts produced
- Metrics logged

## Installation

### Prerequisites

- Python 3.10+
- `uv` package manager (recommended) or pip
- Domino API key
- Access to a Domino deployment

### Setup Steps

```bash
# Clone repository
git clone https://github.com/dominodatalab/domino_mcp_server.git
cd domino_mcp_server

# Install with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the MCP server directory:

```bash
# Required
DOMINO_API_KEY=your_api_key_here
DOMINO_HOST=https://your-domino.company.com

# Optional
DOMINO_PROJECT_OWNER=default_owner
DOMINO_PROJECT_NAME=default_project
```

### Cursor Configuration

Create `.cursor/mcp.json` in your home directory or project:

```json
{
  "mcpServers": {
    "domino": {
      "command": "uv",
      "args": ["run", "domino-mcp-server"],
      "cwd": "/path/to/domino_mcp_server",
      "env": {
        "DOMINO_API_KEY": "your_api_key",
        "DOMINO_HOST": "https://your-domino.company.com"
      }
    }
  }
}
```

### Project Settings File

Create `domino_project_settings.md` in your project root:

```markdown
# Domino Project Settings

## Project Information
- **Project Owner**: your-username
- **Project Name**: my-ml-project

## Environment
- **Compute Environment**: Default Python 3.10
- **Hardware Tier**: small-k8s

## Data Paths
- Training data: /mnt/data/training/
- Model artifacts: /mnt/artifacts/
```

### Cursor Rules File

Create `.cursorrules` for optimized agent behavior:

```text
# Domino Vibe Modeling Rules

When running code in Domino:
1. Always commit changes to git before running jobs
2. Use /mnt/data/ for input data paths
3. Use /mnt/artifacts/ for output artifacts
4. Check job status before requesting results
5. Wait for job completion before analyzing outputs

Data access patterns:
- Project files: /mnt/code/
- Imported datasets: /mnt/imported/data/
- Project datasets: /mnt/data/

Always use relative imports and paths that work in Domino jobs.
```

## Usage Examples

### Running a Training Script

1. Write your training code in the project
2. Commit to git: `git add . && git commit -m "Add training script"`
3. In Cursor, prompt: "Run the training script train.py in Domino"
4. MCP server executes: `python train.py` as a Domino job
5. Check status: "What's the status of my Domino job?"
6. Get results: "Show me the results from the training job"

### Analyzing Data

```
User: Analyze the sales data in /mnt/data/sales.csv and create a summary

Cursor (via MCP):
1. Creates analysis script
2. Commits to git
3. Runs as Domino job
4. Returns results
```

### Experiment Tracking

```python
# train.py (executed as Domino job)
import mlflow

mlflow.set_experiment("vibe-modeling-experiment")

with mlflow.start_run():
    # Training code here
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_metric("accuracy", 0.95)
```

## How It Works

### Request Flow

1. User prompts AI assistant with task
2. AI determines Domino job is needed
3. MCP server receives command via stdin/stdout
4. Server makes authenticated REST API call to Domino
5. Domino creates and runs job in container
6. MCP server polls for completion
7. Results returned to AI assistant
8. AI presents results to user

### Authentication

The MCP server authenticates using:
- `DOMINO_API_KEY` environment variable
- Passed to Domino REST API in headers

### Security

- All code runs in isolated Domino containers
- No local execution of untrusted code
- Full audit trail in Domino
- Version control through git integration

## Troubleshooting

### MCP Server Not Connecting

```bash
# Verify MCP server starts
cd /path/to/domino_mcp_server
uv run domino-mcp-server

# Check for errors in output
```

### Jobs Not Starting

1. Verify API key is valid
2. Check Domino host URL is correct
3. Ensure project owner/name are correct
4. Verify you have job execution permissions

### Uncommitted Changes Error

```
Error: Cannot run job - uncommitted changes detected
```

**Solution:**
```bash
git add .
git commit -m "Prepare for Domino job"
```

Then retry the Domino job.

### Authentication Errors

```
Error: 401 Unauthorized
```

**Solution:**
1. Regenerate Domino API key
2. Update `.env` file
3. Restart Cursor

## Best Practices

1. **Commit Before Running**: Always commit changes to git before running Domino jobs

2. **Use Standard Paths**: Stick to Domino's standard paths:
   - `/mnt/code/` - Project code
   - `/mnt/data/` - Project datasets
   - `/mnt/imported/data/` - Imported datasets
   - `/mnt/artifacts/` - Output artifacts

3. **Check Job Status**: Always check job status before requesting results

4. **Keep Jobs Focused**: Run smaller, focused jobs rather than monolithic scripts

5. **Log Everything**: Use MLflow for experiment tracking within jobs
