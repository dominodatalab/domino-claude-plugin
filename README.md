# Domino Data Lab Plugin for Claude Code

A comprehensive Claude Code plugin providing full coverage of the Domino Data Lab platform for AI-assisted development.

## Overview

This plugin enables Claude Code to help you with all aspects of Domino Data Lab, including:

- **Workspaces**: Jupyter, VS Code, RStudio configuration and management
- **Jobs**: Batch execution, scheduled jobs, and monitoring
- **Environments**: Custom Docker environments and package management
- **Datasets**: Data versioning with snapshots and sharing
- **Apps**: Deploy React, Streamlit, and Dash applications
- **Models**: Deploy, monitor, and manage model endpoints
- **GenAI**: Trace and evaluate AI agents with the Domino SDK
- **Distributed Computing**: Spark, Ray, and Dask clusters
- **And more...**

## Installation

### Prerequisites

- **Claude Code CLI** v1.0.33 or later (`claude --version` to check)
- Access to a Domino Data Lab instance
- Domino API key (for API operations when running outside a Domino workspace)
- **`uv`** package manager ([install guide](https://github.com/astral-sh/uv)) — required for the bundled Domino MCP server

---

### Option 1: Marketplace Install (Recommended)

This approach registers the plugin through Claude Code's native marketplace system so it persists across sessions.

**Step 1: Clone the repository and create a marketplace wrapper**

```bash
# Clone the plugin
git clone https://github.com/dominodatalab/domino-claude-plugin.git

# Create the marketplace directory structure
mkdir -p ~/.claude/marketplaces/domino/.claude-plugin
mkdir -p ~/.claude/marketplaces/domino/plugins

# Move the plugin into the marketplace
mv domino-claude-plugin ~/.claude/marketplaces/domino/plugins/domino-claude-plugin
```

**Step 2: Create the marketplace manifest**

```bash
cat > ~/.claude/marketplaces/domino/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "domino-marketplace",
  "owner": {
    "name": "Domino Data Lab",
    "email": "support@dominodatalab.com"
  },
  "plugins": [
    {
      "name": "domino-claude-plugin",
      "description": "Domino Data Lab plugin for Claude Code - workspaces, jobs, environments, datasets, apps, models, and more",
      "version": "1.0.0",
      "source": "./plugins/domino-claude-plugin",
      "category": "development"
    }
  ]
}
EOF
```

**Step 3: Register the marketplace and install the plugin**

Launch Claude Code and run:

```
/plugin marketplace add /home/<your-username>/.claude/marketplaces/domino
/plugin install domino-claude-plugin@domino-marketplace
```

> **Note:** Replace `<your-username>` with your actual username, or use the full absolute path (e.g., `/home/ubuntu/.claude/marketplaces/domino`). The `~` shorthand may not expand correctly.

**Step 4: Restart Claude Code**

```
/exit
claude
```

The plugin should appear in your loaded plugins on startup. Verify with:

```
/plugin
```

Navigate to the **Installed** tab to confirm `domino-claude-plugin` is listed.

---

### Option 2: Direct Plugin Directory (Development / Quick Start)

Use the `--plugin-dir` flag to load the plugin directly. This is ideal for development, testing, or quick evaluation.

```bash
# Clone the plugin
git clone https://github.com/dominodatalab/domino-claude-plugin.git

# Ensure the plugin manifest exists
mkdir -p domino-claude-plugin/.claude-plugin
cat > domino-claude-plugin/.claude-plugin/plugin.json << 'EOF'
{
  "name": "domino-claude-plugin",
  "description": "Domino Data Lab plugin for Claude Code",
  "version": "1.0.0"
}
EOF

# Run Claude Code with the plugin
claude --plugin-dir ./domino-claude-plugin
```

To make this persistent without the marketplace approach, add a shell alias:

```bash
echo 'alias claude="claude --plugin-dir /path/to/domino-claude-plugin"' >> ~/.bashrc
source ~/.bashrc
```

---

### Option 3: Team / Project-Level Install

For teams sharing a project, add the marketplace to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "domino-marketplace": {
      "source": {
        "source": "directory",
        "path": "/path/to/domino-marketplace"
      }
    }
  },
  "enabledPlugins": {
    "domino-claude-plugin@domino-marketplace": true
  }
}
```

When team members trust the repository folder, Claude Code will prompt them to install the marketplace and plugin automatically.

---

## Verifying the Installation

After installation, test that the plugin is working:

1. **Check slash commands are available:**

   ```
   /domino-app-init
   ```

2. **Test skill auto-invocation** by asking a Domino-related question:

   ```
   Help me deploy a Streamlit app to Domino
   ```

   Claude should automatically invoke the `domino-app-deployment` skill.

3. **Check the plugin is listed:**

   ```
   /plugin
   ```

   Navigate to the **Installed** tab.

> **Note:** Plugin skills do not appear in the `/skills` list. They are auto-invoked by Claude based on task context and will show in Claude's init message at the top of a new session.

---

## Updating the Plugin

If installed via the marketplace approach, navigate to the plugin source and pull updates:

```bash
cd ~/.claude/marketplaces/domino/plugins/domino-claude-plugin
git pull
```

Then restart Claude Code. If installed via `--plugin-dir`, pull updates in the cloned directory.

---

## What's Included

### Bundled MCP Server

The plugin includes a vendored copy of the [Domino MCP Server](https://github.com/dominodatalab/domino_mcp_server) that **starts automatically** when the plugin is enabled. It provides tools for running Domino jobs, checking job status/results, and syncing files with DFS-based projects.

- **Inside a Domino workspace:** Fully automatic — authentication uses ephemeral tokens, project info is auto-detected.
- **Outside Domino (laptop):** Set `DOMINO_API_KEY` and `DOMINO_HOST` as environment variables in your shell.

Requires `uv` to be installed (see [Prerequisites](#prerequisites)).

### Skills (18 Total)

| Skill | Description |
| --- | --- |
| `domino-workspaces` | Jupyter, VS Code, RStudio workspace management |
| `domino-jobs` | Jobs and scheduled jobs execution |
| `domino-environments` | Compute environments and Dockerfile customization |
| `domino-datasets` | Data management, snapshots, and versioning |
| `domino-projects` | Git integration and project collaboration |
| `domino-app-deployment` | Deploy web apps (React, Streamlit, Dash) |
| `domino-experiment-tracking` | MLflow experiment tracking and model registry |
| `domino-genai-tracing` | `@add_tracing` decorator and `DominoRun` |
| `domino-model-endpoints` | Deploy and call model APIs |
| `domino-model-monitoring` | Drift detection and model quality tracking |
| `domino-flows` | Flyte-based workflow orchestration |
| `domino-distributed-computing` | Spark, Ray, Dask cluster management |
| `domino-ai-gateway` | LLM proxy for OpenAI, Bedrock, etc. |
| `domino-launchers` | Parameterized web forms for self-service |
| `domino-modeling-assistant` | MCP server for AI-assisted model development |
| `domino-data-connectivity` | S3 Mountpoint, AWS IRSA, Azure credentials |
| `domino-python-sdk` | Python SDK (python-domino) and REST API |
| `domino-data-sdk` | Data SDK (domino-data) for data sources, datasets, training sets |
| `domino-ui-design` | Knowledge on Domino UI styling for integrated App design |

### Slash Commands

| Command | Description |
| --- | --- |
| `/domino-app-init` | Initialize a new Domino app with framework templates |
| `/domino-debug-proxy` | Debug reverse proxy issues for apps |
| `/domino-experiment-setup` | Set up MLflow experiment tracking |
| `/domino-trace-setup` | Set up GenAI tracing with the Domino SDK |

### Subagents

| Agent | Description |
| --- | --- |
| `domino-deploy` | Specialized agent for deploying apps, models, and endpoints |
| `domino-debug` | Agent for debugging Domino issues and troubleshooting |
| `domino-setup` | Agent for setting up new projects and configurations |

### Output Styles

Switch output styles with `/output-style`:

| Style | Description |
| --- | --- |
| `domino-learning` | Educational mode with Domino Insights after each task |
| `domino-mlops` | Production-focused with MLOps checklists and best practices |

---

## Project Structure

```
domino-claude-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── .mcp.json                # Bundled MCP server config (auto-starts)
├── mcp-servers/             # Vendored MCP servers
│   └── domino_mcp_server/   # Domino MCP Server (jobs, DFS sync)
├── agents/                  # Subagents
│   ├── domino-deploy.md
│   ├── domino-debug.md
│   └── domino-setup.md
├── output-styles/           # Custom output styles
│   ├── domino-learning.md
│   └── domino-mlops.md
├── skills/                  # 18 skill directories
│   ├── workspaces/
│   ├── jobs/
│   ├── environments/
│   ├── datasets/
│   ├── projects/
│   ├── app-deployment/
│   ├── experiment-tracking/
│   ├── genai-tracing/
│   ├── model-endpoints/
│   ├── model-monitoring/
│   ├── flows/
│   ├── distributed-computing/
│   ├── ai-gateway/
│   ├── launchers/
│   ├── modeling-assistant/
│   ├── data-connectivity/
│   ├── python-sdk/
│   └── domino-data-sdk/
├── commands/                # Slash commands
├── hooks/                   # Example automation hooks
├── templates/               # Code templates
│   ├── vite-react/
│   ├── streamlit/
│   ├── dash/
│   ├── experiment/
│   └── tracing/
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

## Troubleshooting

| Issue | Solution |
| --- | --- |
| `/skills` shows "No skills found" | Plugin skills don't appear in `/skills` — they are auto-invoked by Claude based on context. Check `/plugin` → Installed tab instead. |
| Plugin not loading from settings.json | Claude Code does **not** support a `"plugins"` array in `settings.json`. Use the marketplace approach or `--plugin-dir` flag. |
| `~` path not expanding | Always use absolute paths (e.g., `/home/ubuntu/...`) in marketplace commands and settings. |
| Slash commands not appearing | Restart Claude Code after installing. Commands are loaded at session start. |
| "Failed to parse marketplace file" | Ensure `marketplace.json` has the `owner` object and `source` is a string path (e.g., `"./plugins/domino-claude-plugin"`), not a nested object. |

---

## Usage Examples

### Deploy a Streamlit App

```
User: Help me deploy a Streamlit dashboard to Domino
Claude: I'll help you set up a Streamlit app for Domino...
```

### Set Up Experiment Tracking

```
User: /domino-experiment-setup
Claude: I'll configure MLflow experiment tracking for your project...
```

### Create a Scheduled Job

```
User: How do I run a training script every day at midnight?
Claude: I'll show you how to create a scheduled job in Domino...
```

### Deploy a Model API

```
User: I need to deploy my scikit-learn model as an API
Claude: I'll help you create a model endpoint in Domino...
```

---

## API Reference

The `domino-python-sdk` skill includes comprehensive REST API documentation:

- `API-PROJECTS.md` — Projects, collaborators, Git repos
- `API-JOBS.md` — Jobs, logs, scheduled execution
- `API-DATASETS.md` — Datasets, snapshots, permissions
- `API-MODELS.md` — Model APIs, deployments, registry
- `API-ENVIRONMENTS.md` — Environments, revisions
- `API-APPS.md` — Apps, versions, instances
- `API-ADMIN.md` — Users, orgs, hardware tiers

---

## Documentation

- [Domino Documentation](https://docs.dominodatalab.com/en/cloud/user_guide/71a047/what-is-domino/)
- [Domino API Guide](https://docs.dominodatalab.com/en/latest/api_guide/f35c19/api-guide/)
- [Domino Blueprints](https://domino.ai/resources/blueprints)
- [python-domino GitHub](https://github.com/dominodatalab/python-domino)
- [Claude Code Plugin Docs](https://code.claude.com/docs/en/plugins)
- [Claude Code Marketplace Docs](https://code.claude.com/docs/en/plugin-marketplaces)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Support

- For Domino platform issues: [Domino Support](https://support.dominodatalab.com/)
- For plugin issues: [GitHub Issues](https://github.com/dominodatalab/domino-claude-plugin/issues)
