---
name: domino-workspaces
description: Work with Domino Workspaces - interactive development environments including Jupyter, JupyterLab, VS Code, and RStudio. Covers launching workspaces, configuring hardware tiers, environment selection, volume mounting, SSH access, and package installation. Use when setting up development environments, configuring workspace settings, or troubleshooting IDE issues.
---

# Domino Workspaces Skill

## Description
This skill helps users work with Domino Workspaces - interactive development environments for data science work including Jupyter notebooks, JupyterLab, VS Code, and RStudio.

## Activation
Activate this skill when users want to:
- Launch or configure a workspace in Domino
- Work with Jupyter notebooks, VS Code, or RStudio
- Configure workspace settings (hardware tier, environment, volumes)
- Understand workspace persistence and file management
- Use SSH to connect to remote workspaces
- Install packages in workspaces

## Workspace Types

### Available IDEs
Domino provides these default workspace types:
- **Jupyter Notebook**: Classic notebook interface
- **JupyterLab**: Modern Jupyter interface with file browser
- **VS Code**: Full-featured code editor with extensions
- **RStudio**: IDE for R development
- **Custom IDEs**: Can configure additional workspace types

## Launching a Workspace

### Via Domino UI
1. Navigate to your project
2. Click **Workspaces** in the navigation
3. Click **Launch Workspace**
4. Select:
   - **IDE**: Choose Jupyter, VS Code, RStudio, etc.
   - **Hardware Tier**: CPU/memory/GPU resources
   - **Compute Environment**: Docker environment with tools
   - **Volume Size**: Persistent storage (if needed)
5. Click **Launch**

### Via Python SDK
```python
from domino import Domino

domino = Domino("project-owner/project-name")

# Start a workspace
workspace = domino.workspace_start(
    environment_id="env-123",
    hardware_tier_name="small",
    workspace_type="JupyterLab"
)

print(f"Workspace ID: {workspace['workspaceId']}")
```

## File Persistence

### Persistent Directories
Work saved to these directories persists across workspace sessions:
- `/mnt/` - Project files (synced with Domino)
- `/mnt/data/` - Domino Datasets
- `/mnt/artifacts/` - Project artifacts
- `/mnt/imported/` - Imported data

### Home Directory Persistence
Domino 6.1+ supports home directory persistence:
- Installed packages persist across sessions
- User configurations (.bashrc, .vimrc) are retained
- Reduces workspace startup time

## Package Installation

### Temporary (Current Session)
```bash
# Python packages
pip install pandas numpy scikit-learn

# R packages
install.packages("tidyverse")
```

### Persistent (Via Environment)
Add to environment's Dockerfile instructions:
```dockerfile
RUN pip install pandas numpy scikit-learn
```

Or use requirements.txt in your project:
```text
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

## SSH Access to Workspaces

Domino 6.1+ allows SSH connections from local machines:

1. **Enable SSH** in workspace settings
2. **Get connection details** from running workspace
3. **Connect via SSH**:
```bash
ssh -i ~/.ssh/domino_key user@workspace-hostname
```

Benefits:
- Use local IDE (VS Code Remote, PyCharm)
- Access remote compute from local machine
- Browse files locally while computing remotely

## Git Integration in Workspaces

### Using Git
```bash
# Clone a repo in workspace
git clone https://github.com/user/repo.git

# Standard git workflow
git add .
git commit -m "Update model"
git push origin main
```

### Sync with Domino
Click **Sync** in the workspace UI to push changes back to Domino project.

## Workspace Operations

### Stop a Workspace
```python
domino.workspace_stop(workspace_id)
```

### Resume a Workspace
Stopped workspaces can be resumed to continue work.

### View Workspace Logs
Access logs for debugging through the Domino UI or API.

## Best Practices

1. **Save frequently**: Sync work to Domino regularly
2. **Use appropriate hardware**: Match resources to workload
3. **Clean up**: Stop workspaces when not in use to save resources
4. **Version control**: Use Git for code versioning
5. **Environment management**: Use Domino Environments for reproducibility

## Troubleshooting

### Workspace Won't Start
- Check hardware tier availability
- Verify environment builds successfully
- Check resource quotas

### Lost Work
- Check `/mnt/` directories for persisted files
- Review Domino project files
- Check Git history if using version control

### Slow Startup
- Use smaller base environments
- Enable package persistence
- Pre-install packages in environment Dockerfile

## Documentation Reference
- [Use Workspaces](https://docs.dominodatalab.com/en/latest/user_guide/867b72/use-workspaces/)
- [Launch a Workspace](https://docs.dominodatalab.com/en/latest/user_guide/e6e601/workspaces)
- [Start a Jupyter Workspace](https://docs.dominodatalab.com/en/latest/user_guide/93aef2/start-a-jupyter-workspace/)
