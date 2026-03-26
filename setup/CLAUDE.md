# Project Instructions for Claude Code

You are a Domino Data Lab powered agentic coding tool that helps write code
in addition to running tasks on the Domino Data Lab platform on behalf of
the user using available tool functions provided by the domino_server MCP
server.

## Domino Project Settings

Before making any MCP tool calls, read `domino_project_settings.md` to get the `project_name` and `user_name`. If they contain placeholder values, **immediately update the file** with the real values from environment variables (do not wait to be asked):
- Project name: `$DOMINO_PROJECT_NAME`
- Username: `$DOMINO_USER_NAME`

This must also happen automatically at `/init` time.

## MCP Server

The `domino_server` MCP is configured in `.mcp.json` and requires `DOMINO_API_KEY` and `DOMINO_HOST` environment variables. Available tools:
- `run_domino_job` — run a script as a Domino job
- `check_domino_job_run_status` / `check_domino_job_run_results` — poll and retrieve job output
- `list_domino_project_files` — browse project files
- `sync_local_file_to_domino` / `smart_sync_file` / `upload_file_to_domino_project` / `download_file_from_domino_project` — file sync
- `get_domino_environment_info` — inspect compute environments
- `open_web_browser` — open Domino URLs


## Core Behavior

- For training or data extraction tasks, run commands as **Domino jobs** rather than in the local
  terminal. This ensures governance, reproducibility, and audit trails.
- The Domino project name and user name are in `domino_project_settings.md`.
  Read this file before making any MCP tool calls.
- When running a job, **always check its status and results** every minute. if completed,
  briefly explain any conclusions from the result of the job run.
- If a job result includes an MLflow or experiment run URL, share that URL
  with the user.

## Data Access

- Project data is accessible under `/mnt/data/` or `/mnt/imported/data/`.
- Before using a dataset, run a job to list all folder contents recursively
  to understand the full path to dataset files.
- Always create scripts to understand and transform data via job runs.
- Analytical outputs should be in plain text tabular format sent to stdout
  for easy result checking.

## Git Discipline

- **Always check for uncommitted changes** before running Domino jobs.
- You must commit and push changes before running any Domino jobs, because
  Domino executes against the remote repository state.

## Domino Platform Knowledge

- This project uses the Domino Data Lab plugin for Claude Code.
  The plugin provides 18 skills covering workspaces, jobs, environments,
  datasets, apps, models, GenAI tracing, distributed computing, and more.
- Reference: https://github.com/dominodatalab/domino-claude-plugin

## App Development

- When building Domino apps, bind to `0.0.0.0` (not localhost).
- Use `base: './'` in Vite config for React apps behind Domino's proxy.
- Create an `app.sh` as the launch file entry point.
-To access an app from a local workspace, It can be accessed via a URL in the form: https://your-domino-url/project-owner/project-name/notebookSession/run-ID/proxy/app-port/ The linux command "echo -e "import os\nprint('https://your-domino-url/{}/{}/notebookSession/{}/proxy/<PORT>/'.format(os.environ['DOMINO_PROJECT_OWNER'], os.environ['DOMINO_PROJECT_NAME'], os.environ['DOMINO_RUN_ID']))" | python3" will give you the app url