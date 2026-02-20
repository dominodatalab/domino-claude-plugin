---
name: domino-environments
description: Create and customize Domino Compute Environments - Docker containers defining tools, packages, and configurations. Covers Dockerfile customization, package installation, IDE configuration, DSE (Domino Standard Environments), and troubleshooting build failures. Use when installing dependencies, customizing environments, or fixing environment issues.
---

# Domino Compute Environments Skill

## Description
This skill helps users create, customize, and manage Domino Compute Environments - Docker-based containers that define the tools, packages, and configurations for workspaces, jobs, and other executions.

## Activation
Activate this skill when users want to:
- Create or customize a compute environment
- Install packages or dependencies
- Configure Dockerfile instructions
- Understand environment best practices
- Troubleshoot environment build issues

## What is a Compute Environment?

A Domino Compute Environment is a Docker container image that contains:
- Operating system and base tools
- Programming languages (Python, R)
- IDEs (Jupyter, VS Code, RStudio)
- Libraries and packages
- Custom configurations

## Domino Standard Environments (DSEs)

Domino provides pre-built environments with common tools:

| Environment | Includes |
|-------------|----------|
| Domino Standard Environment | Python 3.9, R 4.1, Jupyter, VS Code |
| Domino Spark Environment | Spark 3.x, PySpark |
| Domino Ray Environment | Ray for distributed computing |
| Domino GPU Environment | CUDA, cuDNN, GPU libraries |

## Creating a Custom Environment

### Via Domino UI
1. Go to **Environments** in Domino
2. Click **Create Environment**
3. Configure:
   - **Name**: Descriptive name
   - **Base Image**: Start from DSE or custom image
   - **Dockerfile Instructions**: Add customizations
4. Click **Build**

### Dockerfile Instructions

Add instructions to customize the environment. Do NOT include `FROM` statement.

```dockerfile
# Install system packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    pandas==2.0.0 \
    scikit-learn==1.3.0 \
    tensorflow==2.13.0

# Install R packages
RUN R -e "install.packages(c('tidyverse', 'caret'), repos='https://cloud.r-project.org')"

# Set environment variables
ENV MODEL_PATH=/mnt/artifacts/model.pkl
```

## Package Installation Methods

### Method 1: Dockerfile Instructions (Recommended)
Best for packages that should always be available.

```dockerfile
RUN pip install pandas numpy scikit-learn
```

**Pros**: Fast startup, consistent environment
**Cons**: Requires environment rebuild for changes

### Method 2: requirements.txt
Packages installed at execution startup.

```text
# requirements.txt in project root
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

**Pros**: No rebuild needed, per-project customization
**Cons**: Slower startup

### Method 3: Pre/Post-run Scripts
Custom scripts that run at execution start.

```bash
#!/bin/bash
# pre-run.sh
pip install -q custom-package
```

### Method 4: Runtime Installation
Install during execution (temporary).

```python
!pip install package-name
```

## Dockerfile Best Practices

### Combine RUN Commands
```dockerfile
# Good: Single layer
RUN pip install pandas numpy scikit-learn matplotlib

# Bad: Multiple layers
RUN pip install pandas
RUN pip install numpy
RUN pip install scikit-learn
```

### Clean Up
```dockerfile
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*
```

### Pin Versions
```dockerfile
# Good: Reproducible
RUN pip install pandas==2.0.0 scikit-learn==1.3.0

# Bad: May break
RUN pip install pandas scikit-learn
```

### Use --no-cache-dir
```dockerfile
RUN pip install --no-cache-dir package-name
```

## Environment Variables

### Set in Dockerfile
```dockerfile
ENV MY_VAR=value
ENV DATA_PATH=/mnt/data
```

### Set in Domino UI
1. Go to Environment settings
2. Add environment variables
3. Variables available in all executions

### Access in Code
```python
import os
value = os.environ.get('MY_VAR', 'default')
```

## GPU Environments

### CUDA Setup
```dockerfile
# Ensure base image has CUDA
# Add GPU-specific packages
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### TensorFlow GPU
```dockerfile
RUN pip install tensorflow[and-cuda]
```

### Verify GPU Access
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
```

## IDE Configuration

### Custom Jupyter Config
```dockerfile
RUN mkdir -p /home/domino/.jupyter && \
    echo "c.NotebookApp.token = ''" >> /home/domino/.jupyter/jupyter_notebook_config.py
```

### VS Code Extensions
Pre-install extensions:
```dockerfile
RUN code-server --install-extension ms-python.python
```

## Environment Revisions

Domino tracks environment versions:
- Each build creates a new revision
- Can roll back to previous revisions
- Executions can specify which revision to use

### View Revisions
Go to Environment > **Revisions** tab

### Use Specific Revision
Select revision when launching workspace or job.

## Troubleshooting Builds

### Build Fails
1. Check Dockerfile syntax
2. Verify base image exists
3. Check network access for package downloads
4. Review build logs for specific errors

### Common Errors

**Package not found**:
```dockerfile
# Wrong
RUN pip install sklearn

# Right
RUN pip install scikit-learn
```

**Permission denied**:
```dockerfile
# Run as root if needed
USER root
RUN apt-get update && apt-get install -y package
USER domino
```

**Timeout during build**:
- Reduce number of packages
- Use pre-built wheels
- Check network connectivity

### Test Locally
```bash
# Build and test locally before adding to Domino
docker build -t test-env -f Dockerfile .
docker run -it test-env python -c "import pandas; print(pandas.__version__)"
```

## Best Practices Summary

1. **Start from DSE**: Use Domino Standard Environment as base
2. **Minimize layers**: Combine RUN commands
3. **Pin versions**: Ensure reproducibility
4. **Document changes**: Comment Dockerfile instructions
5. **Test before building**: Verify packages work together
6. **Clean up**: Remove cache and temporary files
7. **Regular updates**: Keep packages current for security

## Documentation Reference
- [Customize your Environment](https://docs.dominodatalab.com/en/latest/user_guide/5dd2c1/customize-your-environment/)
- [Add packages to Environments](https://docs.dominodatalab.com/en/latest/user_guide/bfa148/add-packages-to-environments/)
- [Domino Standard Environments](https://docs.dominodatalab.com/en/latest/user_guide/0d73c6/domino-standard-environments/)
- [Best Practices for Environments](https://docs.dominodatalab.com/en/cloud/user_guide/0e4da9/best-practices-for-domino-environments/)
