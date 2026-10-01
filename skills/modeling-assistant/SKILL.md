---
name: domino-modeling-assistant
description: "Run AI-assisted model training, data analysis, and experiment tracking within Domino Data Lab using the bundled MCP server. Submit training scripts as Domino jobs, check job status and results, sync files to DFS projects, log experiments with MLflow, and open experiment URLs. Works with Claude Code, Cursor, and GitHub Copilot. Use when running a model in Domino, submitting Domino jobs from an AI assistant, training models with MLflow tracking, analyzing project data via job runs, or syncing files to DFS-based Domino projects."
---

# Domino Modeling Assistant

Run code as Domino jobs instead of locally — maintains security, governance, reproducibility, and access to cluster compute resources.

The Domino MCP Server is **bundled with this plugin** and starts automatically. No manual installation or MCP configuration is needed.

- **Inside a Domino workspace:** Authentication and project detection are fully automatic.
- **Outside Domino (laptop):** Set `DOMINO_API_KEY` and `DOMINO_HOST` env vars. See [SETUP.md](./SETUP.md) for details.

## Session Workflow

1. **Detect environment** — call `get_domino_environment_info` at session start. This returns workspace vs laptop mode, project owner/name, DFS vs Git, and auth status.
2. **Sync code before running jobs:**
   - **Git projects:** commit and push all changes first — Domino cannot see uncommitted files.
   - **DFS projects:** use `smart_sync_file` or `upload_file_to_domino_project` instead of git.
3. **Submit job** — call `run_domino_job` with the script command.
4. **Poll status** — call `check_domino_job_run_status` until the job completes or errors.
5. **Retrieve results** — call `check_domino_job_run_results` to get stdout. If the output includes an MLflow experiment URL, open it with `open_web_browser`.

### Data Paths

| Project type | Data location |
|---|---|
| Git-based | `/mnt/data/` or `/mnt/imported/data/` |
| DFS-based | `/domino/datasets/` |

Before using a dataset, run a job to list directory contents recursively to confirm the full path.

### MLflow Integration

MLflow tracking is preconfigured — no URL or server setup needed. Instrument training scripts with `mlflow.autolog()` or manual `mlflow.log_*` calls.

### Key Rules

- Always run analysis scripts as Domino jobs, not locally.
- Output analytical results as plain text tabular format to stdout for easy retrieval.
- Save charts as image files to project files.
- Do not delete analysis or training scripts from the project.
- Inside a workspace, project info is auto-detected via `DOMINO_PROJECT_OWNER` and `DOMINO_PROJECT_NAME` env vars. Outside Domino, fall back to `domino_project_settings.md`.

## MCP Server Tools

The Domino MCP Server (bundled at `mcp-servers/domino_mcp_server/`) provides these tools:

| Tool | Description |
|---|---|
| `get_domino_environment_info` | Detect workspace vs laptop, project info, auth mode |
| `run_domino_job` | Execute commands as Domino jobs |
| `check_domino_job_run_status` | Check if a job is finished, in-progress, or errored |
| `check_domino_job_run_results` | Retrieve stdout results from a completed job |
| `open_web_browser` | Open a URL (e.g. MLflow experiment link) in the browser |
| `list_domino_project_files` | List files in a DFS project |
| `upload_file_to_domino_project` | Upload a file to a DFS project |
| `download_file_from_domino_project` | Download a file from a DFS project |
| `sync_local_file_to_domino` | Read a local file and upload it to a DFS project |
| `smart_sync_file` | Upload with conflict detection for DFS projects |

Upstream source: https://github.com/dominodatalab/domino_mcp_server

## Related Documentation

- [SETUP.md](./SETUP.md) — Complete setup guide (credentials, project settings, testing)
- [Domino Blueprints: Vibe Modeling](https://domino.ai/resources/blueprints/vibe-modeling) — Official documentation
