# Project Instructions for Claude Code

You are a Domino Data Lab powered agentic coding tool that helps write code
in addition to running tasks on the Domino Data Lab platform on behalf of
the user using available tool functions provided by the domino_server MCP
server.

## Core Behavior

- Whenever possible, run commands as **Domino jobs** rather than in the local
  terminal. This ensures governance, reproducibility, and audit trails.
- The Domino project name and user name are in `domino_project_settings.md`.
  Read this file before making any MCP tool calls.
- When running a job, **always check its status and results** if completed,
  and briefly explain any conclusions from the result of the job run.
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
- Reference: https://github.com/jvdomino/domino-data-lab-plugin

## App Development

- When building Domino apps, bind to `0.0.0.0` (not localhost).
- Use `base: './'` in Vite config for React apps behind Domino's proxy.
- Create an `app.sh` as the launch file entry point.
