---
name: domino-vibe-modeling
description: Enable AI-assisted development (vibe modeling) within Domino using MCP (Model Context Protocol) servers. AI coding assistants like Cursor and GitHub Copilot can execute commands as Domino jobs, maintaining security, governance, and reproducibility. Use when setting up AI code assistants to work with Domino, configuring MCP servers, or enabling vibe modeling workflows.
---

# Domino Vibe Modeling Skill

This skill provides comprehensive knowledge for enabling vibe modeling within Domino Data Lab, allowing AI coding assistants to interact with the platform while maintaining security and governance.

## What is Vibe Modeling?

Vibe modeling refers to using AI code assistants to go beyond pure code generation and assist with:
- Experiment setup and configuration
- Data analysis and exploration
- Model training and evaluation
- Results interpretation

All while maintaining the security, governance, and reproducibility offered by the Domino platform.

## Key Components

### MCP (Model Context Protocol)

MCP servers bridge AI coding assistants with the Domino platform:
- Commands run as containerized Domino jobs (not locally)
- All work maintains platform audit trails and version control
- Data access through standardized paths (`/mnt/data/`, `/mnt/imported/data/`)

### Supported AI Assistants

| Assistant | Support Level |
|-----------|---------------|
| Cursor | Primary support with agent mode |
| GitHub Copilot | Supported with MCP integration |
| VSCode | Supported within Domino workspaces |
| JupyterLab | Supported within Domino workspaces |

## Related Documentation

- [MCP-SERVER.md](./MCP-SERVER.md) - Domino MCP Server setup and usage
- [SETUP.md](./SETUP.md) - Complete setup guide for vibe modeling

## Quick Start

### 1. Clone the MCP Server

```bash
git clone https://github.com/dominodatalab/domino_mcp_server.git
cd domino_mcp_server
```

### 2. Install Dependencies

```bash
uv sync  # or pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# .env file
DOMINO_API_KEY=your_api_key
DOMINO_HOST=https://your-domino.company.com
```

### 4. Configure Cursor

Create `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "domino": {
      "command": "uv",
      "args": ["run", "domino-mcp-server"],
      "cwd": "/path/to/domino_mcp_server"
    }
  }
}
```

### 5. Create Project Settings

Create `domino_project_settings.md` in your project:
```markdown
# Domino Project Settings
- Project Owner: your-username
- Project Name: your-project
```

## MCP Server Tools

The Domino MCP Server provides three primary tools:

| Tool | Description |
|------|-------------|
| `run_domino_job` | Execute commands (Python scripts, etc.) as Domino jobs |
| `check_job_status` | Retrieve execution status of specific job runs |
| `check_job_results` | Obtain detailed results and outputs from completed jobs |

## Important Considerations

1. **Git Commits Required**: Changes must be committed to git before running Domino jobs, as remote execution cannot access uncommitted local changes

2. **Firewall Configuration**: Copilot's URLs must be whitelisted for proper functionality

3. **Custom Environment**: Use the `quay.io/domino/field:vibe-modeling` Docker image for vibe modeling workflows

## Blueprint Reference

Official Vibe Modeling Blueprint:
https://domino.ai/resources/blueprints/vibe-modeling

GitHub Repository:
https://github.com/dominodatalab/domino_mcp_server
