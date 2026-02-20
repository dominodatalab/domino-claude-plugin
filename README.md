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

### Option 1: Clone the Repository

```bash
# Clone the plugin
git clone https://github.com/jvdomino/domino-data-lab-plugin.git

# Run Claude Code with the plugin
claude --plugin-dir /path/to/domino-data-lab-plugin
```

### Option 2: Add to Claude Code Settings

Add the plugin path to your Claude Code configuration file (`~/.claude/settings.json`):

```json
{
  "plugins": [
    "/path/to/domino-data-lab-plugin"
  ]
}
```

## Skills (18 Total)

| Skill | Description |
|-------|-------------|
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
| `domino-vibe-modeling` | MCP server for AI-assisted development |
| `domino-data-connectivity` | S3 Mountpoint, AWS IRSA, Azure credentials |
| `domino-python-sdk` | Python SDK (python-domino) and REST API |
| `domino-data-sdk` | Data SDK (domino-data) for data sources, datasets, training sets |
| `domino-ui-design` | Knowledge on Domino UI styling for integrated App design |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/domino-app-init` | Initialize a new Domino app with framework templates |
| `/domino-debug-proxy` | Debug reverse proxy issues for apps |
| `/domino-experiment-setup` | Set up MLflow experiment tracking |
| `/domino-trace-setup` | Set up GenAI tracing with the Domino SDK |

## Subagents

| Agent | Description |
|-------|-------------|
| `domino-deploy` | Specialized agent for deploying apps, models, and endpoints |
| `domino-debug` | Agent for debugging Domino issues and troubleshooting |
| `domino-setup` | Agent for setting up new projects and configurations |

## Output Styles

Switch output styles with `/output-style`:

| Style | Description |
|-------|-------------|
| `domino-learning` | Educational mode with Domino Insights after each task |
| `domino-mlops` | Production-focused with MLOps checklists and best practices |

## Project Structure

```
domino-data-lab-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── .mcp.json                # MCP server configuration
├── agents/                  # Subagents
│   ├── domino-deploy.md     # Deployment agent
│   ├── domino-debug.md      # Debugging agent
│   └── domino-setup.md      # Setup agent
├── output-styles/           # Custom output styles
│   ├── domino-learning.md   # Educational mode
│   └── domino-mlops.md      # MLOps best practices
├── skills/
│   ├── workspaces/          # Workspace management
│   ├── jobs/                # Job execution
│   ├── environments/        # Compute environments
│   ├── datasets/            # Data management
│   ├── projects/            # Project & Git
│   ├── app-deployment/      # Web apps
│   ├── experiment-tracking/ # MLflow
│   ├── genai-tracing/       # Agent tracing
│   ├── model-endpoints/     # Model APIs
│   ├── model-monitoring/    # Drift detection
│   ├── flows/               # Workflows
│   ├── distributed-computing/ # Spark/Ray/Dask
│   ├── ai-gateway/          # LLM proxy
│   ├── launchers/           # Self-service forms
│   ├── vibe-modeling/       # MCP servers
│   ├── data-connectivity/   # Cloud storage
│   ├── python-sdk/          # python-domino SDK
│   └── domino-data-sdk/     # domino-data SDK
├── commands/                # Slash commands
├── hooks/                   # Example automation hooks
│   └── README.md            # Hook documentation
├── templates/               # Code templates
│   ├── vite-react/
│   ├── streamlit/
│   ├── dash/
│   ├── experiment/
│   └── tracing/
├── README.md
├── LICENSE
└── .gitignore
```

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

## API Reference

The `domino-python-sdk` skill includes comprehensive REST API documentation:

- [API-PROJECTS.md](skills/python-sdk/API-PROJECTS.md) - Projects, collaborators, Git repos
- [API-JOBS.md](skills/python-sdk/API-JOBS.md) - Jobs, logs, scheduled execution
- [API-DATASETS.md](skills/python-sdk/API-DATASETS.md) - Datasets, snapshots, permissions
- [API-MODELS.md](skills/python-sdk/API-MODELS.md) - Model APIs, deployments, registry
- [API-ENVIRONMENTS.md](skills/python-sdk/API-ENVIRONMENTS.md) - Environments, revisions
- [API-APPS.md](skills/python-sdk/API-APPS.md) - Apps, versions, instances
- [API-ADMIN.md](skills/python-sdk/API-ADMIN.md) - Users, orgs, hardware tiers

## Requirements

- Claude Code CLI
- Access to a Domino Data Lab instance
- Domino API key (for API operations)

## Documentation

For more information about Domino Data Lab, see:

- [Domino Documentation](https://docs.dominodatalab.com/en/cloud/user_guide/71a047/what-is-domino/)
- [Domino API Guide](https://docs.dominodatalab.com/en/latest/api_guide/f35c19/api-guide/)
- [Domino Blueprints](https://domino.ai/resources/blueprints)
- [python-domino GitHub](https://github.com/dominodatalab/python-domino)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- For Domino platform issues: [Domino Support](https://support.dominodatalab.com/)
- For plugin issues: [GitHub Issues](https://github.com/jvdomino/domino-data-lab-plugin/issues)
