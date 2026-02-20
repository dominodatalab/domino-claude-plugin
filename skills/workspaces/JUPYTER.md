# Jupyter Workspaces in Domino

## Overview

Domino provides both Jupyter Notebook and JupyterLab as workspace options for interactive Python development.

## Jupyter Notebook vs JupyterLab

| Feature | Jupyter Notebook | JupyterLab |
|---------|------------------|------------|
| Interface | Single notebook | Multi-tab IDE |
| File browser | Limited | Full-featured |
| Terminal | No | Yes |
| Extensions | Limited | Extensive |
| Best for | Quick analysis | Full development |

## Starting a Jupyter Workspace

### Via UI
1. Go to **Workspaces** > **Launch Workspace**
2. Select **JupyterLab** or **Jupyter Notebook**
3. Choose hardware tier and environment
4. Click **Launch**

### Via Python SDK
```python
from domino import Domino

domino = Domino("project-owner/project-name")

workspace = domino.workspace_start(
    workspace_type="JupyterLab",
    hardware_tier_name="small",
    environment_id="your-environment-id"
)
```

## Jupyter AI Integration

Domino supports Jupyter AI for in-notebook AI assistance.

### Setup
1. Use an environment with Jupyter AI installed
2. Configure AI provider credentials
3. Access via magic commands

### Usage
```python
# In a notebook cell
%ai ask "How do I load a CSV file?"

# Chat interface
%ai chat "Explain this error"
```

### Configure Provider
```python
%ai config --provider openai --model gpt-4
```

## Working with Notebooks

### Create New Notebook
1. In JupyterLab: **File** > **New** > **Notebook**
2. Select Python kernel

### Save and Sync
- Notebooks in `/mnt/` auto-sync to Domino
- Click **Sync** to manually push changes
- Use Git for version control

### Run Cells
- `Shift+Enter`: Run cell and move to next
- `Ctrl+Enter`: Run cell in place
- `Alt+Enter`: Run cell and insert new below

## Notebook Best Practices

### Structure
```python
# Cell 1: Imports
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Cell 2: Configuration
DATA_PATH = "/mnt/data/dataset.csv"
MODEL_PATH = "/mnt/artifacts/model.pkl"

# Cell 3: Load Data
df = pd.read_csv(DATA_PATH)

# Cell 4+: Analysis and modeling
```

### Documentation
Use Markdown cells for documentation:
```markdown
# Model Training

## Overview
This notebook trains a classification model on customer data.

## Data Sources
- `/mnt/data/customers.csv`: Customer features
- `/mnt/data/labels.csv`: Target labels
```

## Environment Variables

Access Domino environment variables in notebooks:
```python
import os

# Domino-provided variables
project_name = os.environ.get('DOMINO_PROJECT_NAME')
run_id = os.environ.get('DOMINO_RUN_ID')
username = os.environ.get('DOMINO_USER_NAME')

# Custom environment variables (set in project settings)
api_key = os.environ.get('MY_API_KEY')
```

## Accessing Data

### Domino Datasets
```python
# Datasets are mounted at /mnt/data/{dataset-name}
df = pd.read_csv("/mnt/data/my-dataset/data.csv")
```

### Project Files
```python
# Project files in /mnt/
df = pd.read_csv("/mnt/code/data/input.csv")
```

### External Data
```python
# Use data source connectors
from domino_data.data_sources import DataSourceClient

client = DataSourceClient()
df = client.get_datasource("my-datasource").get_as_df(
    "SELECT * FROM customers"
)
```

## Saving Results

### Artifacts
```python
import joblib

# Save model to artifacts (persisted)
joblib.dump(model, "/mnt/artifacts/model.joblib")
```

### Output Files
```python
# Save to project (synced)
df.to_csv("/mnt/results/predictions.csv")
```

## Converting Notebooks to Scripts

### For Scheduled Jobs
Convert notebook to Python script:
```bash
jupyter nbconvert --to script notebook.ipynb
```

### Using Papermill
Run notebooks programmatically:
```python
import papermill as pm

pm.execute_notebook(
    'input_notebook.ipynb',
    'output_notebook.ipynb',
    parameters={'data_path': '/mnt/data/new_data.csv'}
)
```

## Troubleshooting

### Kernel Dies
- Check memory usage in Domino UI
- Use larger hardware tier
- Optimize code to reduce memory

### Package Not Found
```python
# Install in notebook (temporary)
!pip install package-name

# For persistence, add to environment
```

### Notebook Won't Open
- Check file permissions
- Verify notebook JSON is valid
- Try opening in text editor first

## Documentation Reference
- [Start a Jupyter Workspace](https://docs.dominodatalab.com/en/latest/user_guide/93aef2/start-a-jupyter-workspace/)
- [Set up Jupyter AI](https://docs.dominodatalab.com/en/latest/user_guide/1f4149/set-up-jupyter-ai-in-jupyter-environment/)
