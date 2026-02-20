---
name: domino-jobs
description: Create, run, and manage Domino Jobs - batch executions for scripts, training, and data processing. Covers job configuration, hardware tiers, scheduled jobs (cron), monitoring status, viewing logs, and API-driven execution. Use when running batch workloads, scheduling recurring tasks, or automating training pipelines.
---

# Domino Jobs Skill

## Description
This skill helps users create, run, and manage Domino Jobs - batch executions for running scripts, training models, and processing data.

## Activation
Activate this skill when users want to:
- Run a script or notebook as a batch job
- Schedule recurring jobs
- Configure job settings (hardware, environment)
- Monitor job status and results
- Run jobs via API or CLI

## What is a Domino Job?

A Job is a batch execution that runs a script or command in Domino. Unlike workspaces, jobs:
- Run to completion without user interaction
- Are fully reproducible with tracked inputs/outputs
- Can be scheduled to run automatically
- Scale to any hardware tier

## Creating and Running Jobs

### Via Domino UI
1. Navigate to your project
2. Click **Jobs** in the navigation
3. Click **Run**
4. Configure:
   - **File to Run**: Script path (e.g., `train.py`)
   - **Arguments**: Command-line arguments (optional)
   - **Hardware Tier**: Select resources
   - **Compute Environment**: Select environment
5. Click **Start**

### Via Python SDK
```python
import os
from domino import Domino

domino = Domino(
    "project-owner/project-name",
    api_key=os.environ["DOMINO_USER_API_KEY"],
    host=os.environ["DOMINO_API_HOST"],
)

# Blocking execution - waits for job to complete
domino_run = domino.runs_start_blocking(
    ["train.py", "--epochs", "100"],
    title="Training run from Python SDK"
)
print(domino_run)

# Non-blocking execution - returns immediately
domino_run = domino.runs_start(
    ["train.py", "--epochs", "100"],
    title="Training run from Python SDK"
)
print(f"Job ID: {domino_run['runId']}")

# Check status of non-blocking run
run_status = domino.runs_status(domino_run.get("runId"))
print(f"Status: {run_status['status']}")
```

**Note:** Environment variables `DOMINO_USER_API_KEY` and `DOMINO_API_HOST` are automatically configured when running within Domino workspaces or jobs.

### Via Domino CLI
```bash
# Start a job with script
domino run train.py

# Run with arguments
domino run train.py arg1 arg2 arg3

# Wait for job to complete
domino run --wait train.py arg1 arg2

# Run direct command (not a script)
domino run --direct "pip freeze | grep pandas"
```

### Via REST API
```bash
curl -X POST "https://your-domino.com/v4/projects/{project_id}/runs" \
  -H "X-Domino-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python train.py",
    "hardwareTierId": "tier-id",
    "environmentId": "env-id"
  }'
```

## Job Commands

### Run Python Script
```bash
python train.py
```

### Run with Arguments
```bash
python train.py --data /mnt/data/train.csv --output /mnt/artifacts/model.pkl
```

### Run Jupyter Notebook
```bash
jupyter nbconvert --to notebook --execute notebook.ipynb
```

### Run R Script
```bash
Rscript analysis.R
```

### Run Shell Script
```bash
bash pipeline.sh
```

## Scheduled Jobs

### Creating a Scheduled Job

1. Go to **Scheduled Jobs** in your project
2. Click **New Scheduled Job**
3. Configure:
   - **Name**: Descriptive name
   - **Command**: Script to execute
   - **Schedule**: Cron expression or preset
   - **Hardware Tier**: Resources to use
   - **Environment**: Compute environment

### Schedule Examples

| Schedule | Cron Expression |
|----------|-----------------|
| Every hour | `0 0 * * * ?` |
| Daily at midnight | `0 0 0 * * ?` |
| Every Monday 9 AM | `0 0 9 ? * MON` |
| First of month | `0 0 0 1 * ?` |

### Cron Expression Format
```
┌───────────── second (0-59)
│ ┌───────────── minute (0-59)
│ │ ┌───────────── hour (0-23)
│ │ │ ┌───────────── day of month (1-31)
│ │ │ │ ┌───────────── month (1-12)
│ │ │ │ │ ┌───────────── day of week (0-7, SUN-SAT)
│ │ │ │ │ │
* * * * * *
```

### Run Modes

**Sequential**: Wait for previous job to complete before starting next
```python
# Good for jobs that depend on previous output
# Example: Daily model retrain that uses previous day's data
```

**Concurrent**: Allow multiple jobs to run simultaneously
```python
# Good for independent jobs
# Example: Hourly data refresh that doesn't depend on previous runs
```

## Job Notifications

### Email Notifications
Configure in job settings:
- Success notifications
- Failure notifications
- Specific email addresses

### Model API Updates
Trigger Model API republish after job completes:
1. In scheduled job settings
2. Select **Update Model API** option
3. Choose the Model API to update

## Accessing Job Results

### Output Files
Files written to `/mnt/` directories are available after job completion:
- `/mnt/results/` - Custom outputs
- `/mnt/artifacts/` - Model artifacts

### Job Logs
View logs in Domino UI or via API:
```python
# Get job logs
logs = domino.runs_get_logs(run_id)
print(logs)
```

### Stdout/Stderr
All print statements and errors are captured in job logs.

## Environment Variables in Jobs

```python
import os

# Domino-provided
run_id = os.environ.get('DOMINO_RUN_ID')
project_name = os.environ.get('DOMINO_PROJECT_NAME')
username = os.environ.get('DOMINO_USER_NAME')

# Custom (set in project or job settings)
api_key = os.environ.get('MY_API_KEY')
```

## Job Best Practices

### 1. Parameterize Scripts
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--data-path', required=True)
parser.add_argument('--model-output', required=True)
parser.add_argument('--epochs', type=int, default=100)
args = parser.parse_args()
```

### 2. Log Progress
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting training...")
logger.info(f"Epoch {epoch}/{total_epochs}")
logger.info("Training complete!")
```

### 3. Handle Failures Gracefully
```python
try:
    train_model(data)
except Exception as e:
    logger.error(f"Training failed: {e}")
    # Save checkpoint
    save_checkpoint(model, "checkpoint.pt")
    raise
```

### 4. Save Artifacts
```python
import joblib

# Save model
joblib.dump(model, "/mnt/artifacts/model.joblib")

# Save metrics
with open("/mnt/artifacts/metrics.json", "w") as f:
    json.dump(metrics, f)
```

## Monitoring Jobs

### Job Status
- **Pending**: Waiting for resources
- **Running**: Currently executing
- **Succeeded**: Completed successfully
- **Failed**: Exited with error
- **Stopped**: Manually cancelled

### Check Status via API
```python
status = domino.runs_status(run_id)
print(f"Status: {status['status']}")
print(f"Started: {status['startedAt']}")
```

### Stop a Running Job
```python
domino.runs_stop(run_id)
```

## Troubleshooting

### Job Fails Immediately
- Check script syntax
- Verify file paths exist
- Check environment has required packages

### Job Times Out
- Increase hardware tier resources
- Optimize code performance
- Check for infinite loops

### Out of Memory
- Use larger hardware tier
- Optimize data loading (chunking, generators)
- Clear variables when no longer needed

## Documentation Reference
- [Create and run Jobs](https://docs.dominodatalab.com/en/latest/user_guide/af97b7/create-and-run-jobs/)
- [Scheduled Jobs](https://docs.dominodatalab.com/en/latest/user_guide/673577/scheduled-jobs/)
- [Work with Jobs](https://docs.dominodatalab.com/en/latest/user_guide/942549/work-with-jobs/)
