# Complete Vibe Modeling Setup Guide

This guide walks through setting up vibe modeling with Domino from scratch.

## Prerequisites

- Domino Data Lab account with API access
- Cursor IDE (or compatible MCP-enabled assistant)
- Python 3.10+
- Git
- `uv` package manager (recommended)

## Step 1: Get Domino Credentials

### Generate API Key

1. Log into Domino
2. Go to **Account Settings** (click your profile icon)
3. Navigate to **API Keys**
4. Click **Generate New Key**
5. Copy and save the key securely

### Note Your Domino URL

Your Domino URL is the base URL you use to access the platform:
- Example: `https://domino.company.com`
- Example: `https://your-team.domino.tech`

## Step 2: Clone and Configure MCP Server

### Clone Repository

```bash
cd ~/projects  # or your preferred location
git clone https://github.com/dominodatalab/domino_mcp_server.git
cd domino_mcp_server
```

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Create Environment File

```bash
cat > .env << 'EOF'
DOMINO_API_KEY=your_api_key_here
DOMINO_HOST=https://your-domino.company.com
EOF
```

Replace with your actual values.

### Verify Installation

```bash
uv run domino-mcp-server --help
```

## Step 3: Configure Cursor IDE

### Create MCP Configuration

Create the Cursor MCP config directory if it doesn't exist:

```bash
mkdir -p ~/.cursor
```

Create or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "domino": {
      "command": "uv",
      "args": ["run", "domino-mcp-server"],
      "cwd": "/Users/yourname/projects/domino_mcp_server"
    }
  }
}
```

**Important:** Update the `cwd` path to match your MCP server location.

### Restart Cursor

1. Quit Cursor completely
2. Reopen Cursor
3. Verify connection: **Settings** → **Context** → **Model Context Protocol**

You should see "domino" listed as a connected MCP server.

## Step 4: Configure Your Project

### Create Project Settings

In your Domino project directory, create `domino_project_settings.md`:

```markdown
# Domino Project Settings

## Project Information
- **Project Owner**: your-username
- **Project Name**: your-project-name

## Default Configuration
- **Compute Environment**: Default Python 3.10
- **Hardware Tier**: small-k8s

## Data Locations
- Input data: /mnt/data/
- Imported datasets: /mnt/imported/data/
- Output artifacts: /mnt/artifacts/

## Notes
- Always commit changes before running Domino jobs
- Use MLflow for experiment tracking
```

### Create Cursor Rules (Optional)

Create `.cursorrules` in your project:

```text
# Domino Vibe Modeling Rules

## Before Running Jobs
- Commit all changes to git
- Verify file paths use Domino mount points

## Data Paths
- /mnt/code/ - Your project files
- /mnt/data/ - Project datasets
- /mnt/imported/data/ - Imported datasets
- /mnt/artifacts/ - Save outputs here

## Best Practices
- Use MLflow for experiment tracking
- Keep jobs focused and modular
- Check job status before requesting results
- Handle errors gracefully

## When Writing Code
- Use relative imports
- Don't hardcode local paths
- Include requirements.txt for dependencies
```

## Step 5: Test the Integration

### Create a Test Script

In your project, create `test_domino.py`:

```python
import os
print("Hello from Domino!")
print(f"Project: {os.environ.get('DOMINO_PROJECT_NAME', 'unknown')}")
print(f"User: {os.environ.get('DOMINO_STARTING_USERNAME', 'unknown')}")
```

### Commit the Script

```bash
git add test_domino.py
git commit -m "Add test script for vibe modeling"
git push
```

### Run via Cursor

In Cursor, prompt:
```
Run test_domino.py as a Domino job
```

The MCP server should:
1. Create a Domino job
2. Execute the script
3. Return the output

## Step 6: Set Up Domino Environment (Optional)

For the full vibe modeling experience, use the custom environment.

### Using the Vibe Modeling Image

In your Domino project:

1. Go to **Settings** → **Compute Environment**
2. Create new environment with base image:
   ```
   quay.io/domino/field:vibe-modeling
   ```

This image includes:
- MCP server dependencies
- Common ML libraries
- Preconfigured for vibe modeling

## Workflow Example

### Complete Vibe Modeling Session

1. **Start in Cursor** with your project open

2. **Analyze data** (prompt):
   ```
   Load the sales data from /mnt/data/sales.csv and show me
   a summary of the key metrics
   ```

3. **Cursor creates script**, commits, runs in Domino

4. **Review results** returned through MCP

5. **Iterate on analysis** (prompt):
   ```
   Now create a visualization of sales by region and save it
   to /mnt/artifacts/sales_by_region.png
   ```

6. **Train a model** (prompt):
   ```
   Train a random forest model to predict sales using the
   processed data. Log the results to MLflow.
   ```

7. **All work is tracked** in Domino's experiment manager

## Troubleshooting

### "MCP server not found"

1. Check `~/.cursor/mcp.json` exists
2. Verify `cwd` path is correct
3. Ensure `uv` is installed and in PATH
4. Restart Cursor

### "Unauthorized" errors

1. Verify API key in `.env`
2. Check Domino URL is correct
3. Ensure API key has necessary permissions

### "Project not found"

1. Check `domino_project_settings.md` exists
2. Verify project owner and name are correct
3. Ensure you have access to the project

### Jobs fail immediately

1. Check compute environment is available
2. Verify hardware tier is valid
3. Review Domino job logs for errors

## Next Steps

- [MCP-SERVER.md](./MCP-SERVER.md) - Deep dive into MCP server tools
- [SKILL.md](./SKILL.md) - Overview of vibe modeling capabilities
- [Domino Blueprints](https://domino.ai/resources/blueprints/vibe-modeling) - Official documentation
