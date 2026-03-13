# Vendored from https://github.com/dominodatalab/domino_mcp_server
# MCP Server functions that wrap the Domino API
# Domino API docs, run a job example: https://docs.dominodatalab.com/en/latest/api_guide/8c929e/rest-api-reference/#_startJob

from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
import requests
import asyncio
import os
from dotenv import load_dotenv
import re
import webbrowser
import urllib.parse

load_dotenv()


def _is_domino_workspace() -> bool:
    """Detect whether we're running inside a Domino workspace."""
    return bool(os.environ.get("DOMINO_API_HOST"))


def _get_domino_host() -> str:
    """
    Return the base URL for Domino API calls.

    Inside a Domino workspace the platform provides DOMINO_API_HOST.
    Outside (laptop), we fall back to DOMINO_HOST from the .env file.
    """
    if _is_domino_workspace():
        return os.environ["DOMINO_API_HOST"].rstrip("/")
    host = os.getenv("DOMINO_HOST")
    if not host:
        raise ValueError("DOMINO_HOST environment variable not set.")
    return host.rstrip("/")


def _get_auth_headers() -> dict:
    """
    Return authentication headers for Domino API calls.

    Inside a Domino workspace we obtain a short-lived token from the local
    token endpoint on every call (the token expires very quickly).
    An API_KEY_OVERRIDE env-var is also honoured for local dev inside Domino.

    Outside Domino we use the classic DOMINO_API_KEY from .env.
    """
    # Explicit override always wins (useful for debugging inside Domino)
    api_key_override = os.environ.get("API_KEY_OVERRIDE")
    if api_key_override:
        return {"X-Domino-Api-Key": api_key_override}

    if _is_domino_workspace():
        resp = requests.get("http://localhost:8899/access-token")
        resp.raise_for_status()
        token = resp.text.strip()
        if token.startswith("Bearer "):
            return {"Authorization": token}
        return {"Authorization": f"Bearer {token}"}

    # Legacy: running on a laptop with an API key in .env
    api_key = os.getenv("DOMINO_API_KEY")
    if not api_key:
        raise ValueError("DOMINO_API_KEY environment variable not set.")
    return {"X-Domino-Api-Key": api_key}


def _get_workspace_project_info() -> dict | None:
    """
    When running inside a Domino workspace, return the auto-detected project
    owner and project name from the platform-provided env vars.
    Returns None when not inside a Domino workspace.
    """
    if not _is_domino_workspace():
        return None
    owner = os.environ.get("DOMINO_PROJECT_OWNER")
    name = os.environ.get("DOMINO_PROJECT_NAME")
    if owner and name:
        return {"user_name": owner, "project_name": name}
    return None

# Initialize the Fast MCP server
mcp = FastMCP("domino_server")

def _validate_url_parameter(param_value: str, param_name: str) -> str:
    """
    Validates and URL-encodes a parameter for safe use in URLs.
    Supports international characters by encoding them properly.
    
    Args:
        param_value (str): The parameter value to validate and encode
        param_name (str): The name of the parameter (for error messages)
        
    Returns:
        str: The URL-encoded parameter value
        
    Raises:
        ValueError: If the parameter contains unsafe URL characters
    """
    # Basic safety check - reject if contains dangerous chars that could break URL structure
    if any(char in param_value for char in ['/', '\\', '?', '#', '&', '=', '%']):
        raise ValueError(f"Invalid {param_name}: '{param_value}' contains unsafe URL characters")
    
    # URL encode to handle international characters safely
    return urllib.parse.quote(param_value, safe='')

def _filter_domino_stdout(stdout_text: str) -> str:
    """
    Filters the stdout text from a Domino job run to extract the relevant output.
    It tries to extract text between known infrastructure markers, but falls back
    to returning the full stdout if markers aren't found.
    
    Note: Git and DFS projects have different paths:
    - Git projects: /mnt/artifacts/.domino/configure-spark-defaults.sh
    - DFS projects: /mnt/.domino/configure-spark-defaults.sh
    """
    # Start marker patterns (regex) - handles both Git and DFS project paths
    start_patterns = [
        r"### Completed /mnt(?:/artifacts)?/\.domino/configure-spark-defaults\.sh ###",
        r"### Starting user code ###",
        r"Starting job\.\.\.",
    ]
    
    # End marker patterns (regex)
    end_patterns = [
        r"Evaluating cleanup command on EXIT",
        r"### User code finished ###",
        r"Job completed",
    ]
    
    # Try to find a matching start marker using regex
    start_index = 0
    for pattern in start_patterns:
        match = re.search(pattern, stdout_text)
        if match:
            start_index = match.end()
            break
    
    # Try to find a matching end marker using regex
    end_index = len(stdout_text)
    for pattern in end_patterns:
        match = re.search(pattern, stdout_text[start_index:])
        if match:
            end_index = start_index + match.start()
            break
    
    # Extract and clean the text
    filtered_text = stdout_text[start_index:end_index].strip()
    
    # If we couldn't extract anything meaningful (markers not found, empty result),
    # return the full stdout rather than an error message
    if not filtered_text:
        # Return the raw stdout, just trimmed of whitespace
        return stdout_text.strip() if stdout_text.strip() else "(No output captured)"
    
    return filtered_text

def _extract_and_format_mlflow_url(text: str, user_name: str, project_name: str) -> str | None:
    """
    Finds an MLflow URL in the format http://127.0.0.1:8768/#/experiments/.../runs/...
    and reformats it to the Domino Cloud URL format.
    """
    # Regex to find the specific MLflow URL pattern
    pattern = r"http://127\.0\.0\.1:8768/#/experiments/(\d+)/runs/([a-f0-9]+)"
    match = re.search(pattern, text)

    if match:
        experiment_id = match.group(1)
        run_id = match.group(2)
        # Construct the new URL
        new_url = f"{_get_domino_host()}/experiments/{user_name}/{project_name}/{experiment_id}/{run_id}"
        return new_url
    else:
        return None # Return None if the pattern is not found

def _get_project_id(user_name: str, project_name: str) -> str | None:
    """
    Gets the project ID for a given user and project name.
    
    When running inside Domino, uses the DOMINO_PROJECT_ID environment variable
    (automatically provided by the platform). Otherwise, falls back to looking
    up the project via the gateway API.
    
    Args:
        user_name: The username of the project owner
        project_name: The name of the project
        
    Returns:
        The project ID string, or None if not found
    """
    # First, check if running inside Domino (platform provides project ID)
    domino_project_id = os.getenv("DOMINO_PROJECT_ID")
    if domino_project_id:
        return domino_project_id
    
    # Fall back to API lookup when running outside Domino (e.g., laptop)
    headers = {**_get_auth_headers(), "Content-Type": "application/json"}
    
    url = f"{_get_domino_host()}/v4/gateway/projects"
    params = {"relationship": "Owned"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        projects = response.json()
        
        for project in projects:
            if project.get('name') == project_name:
                return project.get('id')
                
        # If not in owned, try all projects the user has access to
        params = {"relationship": "All"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        projects = response.json()
        
        for project in projects:
            if project.get('name') == project_name:
                return project.get('id')
                
    except requests.exceptions.RequestException:
        pass
        
    return None

@mcp.tool()
async def check_domino_job_run_results(user_name: str, project_name: str, run_id: str) -> Dict[str, Any]:
    """
    Returns the stdout results from a Domino job run.

    Args:
        user_name (str): The user name associated with the Domino Project
        project_name (str): The name of the Domino project.
        run_id (str): The run id of the job run to return the status of
    """
    # Validate and encode input parameters
    encoded_user_name = _validate_url_parameter(user_name, "user_name")
    encoded_project_name = _validate_url_parameter(project_name, "project_name")
    encoded_run_id = _validate_url_parameter(run_id, "run_id")
    
    api_url = f"{_get_domino_host()}/v1/projects/{encoded_user_name}/{encoded_project_name}/run/{encoded_run_id}/stdout"
    headers = _get_auth_headers()
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        raw_stdout = response.json().get('stdout', '') # Use .get for safety
        
        # Initial filtering between markers
        initially_filtered_stdout = _filter_domino_stdout(raw_stdout)
        
        # Attempt to extract and format the MLflow URL
        mlflow_url = _extract_and_format_mlflow_url(initially_filtered_stdout, user_name, project_name)
        
        final_filtered_stdout = initially_filtered_stdout
        # If MLflow URL was found, remove the original URL line(s) from the results
        if mlflow_url:
            # Define the pattern for the original local MLflow URL (run-specific)
            local_mlflow_run_pattern = r"http://127\.0\.0\.1:8768/#/experiments/\d+/runs/[a-f0-9]+"
            # Define the pattern for the experiment link
            local_mlflow_experiment_pattern = r"View experiment at: http://127\.0\.0\.1:8768/#/experiments/\d+"
            
            # Split into lines, filter out lines containing either pattern, and rejoin
            lines = initially_filtered_stdout.splitlines()
            filtered_lines = [line for line in lines if not re.search(local_mlflow_run_pattern, line) and not re.search(local_mlflow_experiment_pattern, line)]
            final_filtered_stdout = "\n".join(filtered_lines).strip()

        # Construct the result dictionary
        result = {"results": final_filtered_stdout}
        if mlflow_url:
             result["mlflow_url"] = mlflow_url # Add the formatted URL if found
             
    except requests.exceptions.RequestException as e:
        result = {"error": f"API request failed: {e}"}
    except Exception as e:
        result = {"error": f"An unexpected error occurred: {e}"}

    return result

@mcp.tool()
async def check_domino_job_run_status(user_name: str, project_name: str, run_id: str) -> Dict[str, Any]:
    """
    The check_domino_job_run_status function checks the status of a job run to determine if its finished or in-progress or had an error. A run can sometimes take 1 or more minutes, so it might be necessary to call this a few times until it's finished before using a different function to read the results.

    Args:
        user_name (str): The user name associated with the Domino Project
        project_name (str): The name of the Domino project.
        run_id (str): The run id of the job run to return the status of
    """
    # Validate and encode input parameters
    encoded_user_name = _validate_url_parameter(user_name, "user_name")
    encoded_project_name = _validate_url_parameter(project_name, "project_name")
    encoded_run_id = _validate_url_parameter(run_id, "run_id")
    
    api_url = f"{_get_domino_host()}/v1/projects/{encoded_user_name}/{encoded_project_name}/runs/{encoded_run_id}"
    headers = _get_auth_headers()
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()
    except requests.exceptions.RequestException as e:
        result = {"error": f"API request failed: {e}"}
    except Exception as e:
        result = {"error": f"An unexpected error occurred: {e}"}

    return result

@mcp.tool()
async def run_domino_job(user_name: str, project_name: str, run_command: str, title: str) -> Dict[str, Any]:
    """
    The run_domino_job function runs a command as a job on the domino data science platform, typically a python script such a 'python my_script.py --arg1 arv1_val --arg2 arv2_val' on the Domino cloud platform.

    Args:
        user_name (str): The user name associated with the Domino project.
        project_name (str): The name of the Domino project.
        run_command (str): The command to run on the domino platform. Example: 'python my_script.py --arg1 arv1_val --arg2 arv2_val'
        title (str): A title of the job that helps later identify the job. Example: 'running training.py script'
    """
    # Validate and encode input parameters
    encoded_user_name = _validate_url_parameter(user_name, "user_name")
    encoded_project_name = _validate_url_parameter(project_name, "project_name")
  
    # Construct the API URL
    # must be in this format: https://domino.host/v1/projects/user_name/project_name/runs
    api_url = f"{_get_domino_host()}/v1/projects/{encoded_user_name}/{encoded_project_name}/runs"

    # Prepare the request headers
    headers = {**_get_auth_headers(), "Content-Type": "application/json"}

    # Prepare the request body according to the specified requirements
    # for the /v1/projects/{user_name}/{project_name}/runs endpoint.
    payload = {
        "command": run_command.split(), # Split the command string into a list
        "isDirect": False, # Matching successful curl command
        "title": title,
        "publishApiEndpoint": False,
    }


    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()
    except requests.exceptions.RequestException as e:
        result = {"error": f"API request failed: {e}"}
    except Exception as e:
        result = {"error": f"An unexpected error occurred: {e}"}

    return result

@mcp.tool()
def open_web_browser(url: str) -> bool:
    """Opens the specified URL in the default web browser.

    Args:
        url: The URL to open.

    Returns:
        True if the browser was opened successfully, False otherwise.
    """
    try:
        webbrowser.open_new_tab(url)
        return True
    except webbrowser.Error:
        return False


@mcp.tool()
async def get_domino_environment_info() -> Dict[str, Any]:
    """
    Returns information about the current Domino environment.
    Use this at the start of a session to auto-detect the project owner,
    project name, whether this is a DFS or Git project, and what
    authentication mode is in use.

    When running inside a Domino workspace most settings are detected
    automatically from platform-provided environment variables.
    When running outside Domino (e.g. on a laptop) the response will
    indicate that a domino_project_settings.md file should be consulted.
    """
    import subprocess

    info: Dict[str, Any] = {
        "inside_domino_workspace": _is_domino_workspace(),
        "domino_host": _get_domino_host(),
    }

    if _is_domino_workspace():
        info["user_name"] = os.environ.get("DOMINO_PROJECT_OWNER", "")
        info["project_name"] = os.environ.get("DOMINO_PROJECT_NAME", "")
        info["auth_mode"] = "ephemeral_token"

        # Auto-detect DFS vs Git by probing for a git repo
        try:
            result = subprocess.run(
                ["git", "status"],
                capture_output=True, text=True, timeout=5,
            )
            info["is_dfs_project"] = result.returncode != 0
        except Exception:
            info["is_dfs_project"] = True
    else:
        info["auth_mode"] = "api_key"
        info["note"] = (
            "Running outside Domino. Consult domino_project_settings.md "
            "for project owner, project name, and DFS settings."
        )

    return info


# ============================================================================
# DFS (Domino File System) File Sync Tools
# These tools support syncing files with non-git Domino projects that use DFS
# ============================================================================

# In-memory cache to track file versions we've seen
# Key: (user_name, project_name, file_path) -> {"key": str, "content": str}
_file_version_cache: Dict[tuple, Dict[str, Any]] = {}


def _get_remote_file_info(user_name: str, project_name: str, file_path: str) -> Dict[str, Any] | None:
    """
    Gets the current remote file info (key, size) without downloading content.
    Returns None if file doesn't exist.
    """
    headers = {**_get_auth_headers(), "Content-Type": "application/json"}
    
    url = f"{_get_domino_host()}/v4/files/browseFiles"
    params = {
        "ownerUsername": user_name,
        "projectName": project_name,
        "filePath": "/"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        files = response.json()
        
        for f in files:
            if f.get("path") == file_path:
                return {
                    "key": f.get("key"),
                    "size": f.get("size"),
                    "lastModified": f.get("lastModified")
                }
        return None
    except:
        return None


@mcp.tool()
async def list_domino_project_files(user_name: str, project_name: str, path: str = "/") -> Dict[str, Any]:
    """
    Lists files in a Domino project directory. Works with DFS (non-git) projects.
    Use this to see what files exist in a Domino project before uploading or downloading.

    Args:
        user_name (str): The username of the project owner (e.g., 'etan_lightstone')
        project_name (str): The name of the Domino project (e.g., 'diabetes_dfs_proj')
        path (str): The directory path to list files from (default: "/" for root)

    Returns:
        Dict containing 'files' list with file info (path, size, lastModified, key)
        or 'error' if the operation failed.
    """
    headers = {**_get_auth_headers(), "Content-Type": "application/json"}
    
    # Use browseFiles endpoint to list files
    url = f"{_get_domino_host()}/v4/files/browseFiles"
    params = {
        "ownerUsername": user_name,
        "projectName": project_name,
        "filePath": path
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        files = response.json()
        
        # Simplify the response for easier consumption
        simplified_files = []
        for f in files:
            simplified_files.append({
                "path": f.get("path"),
                "name": f.get("name"),
                "size": f.get("size"),
                "lastModified": f.get("lastModified"),
                "key": f.get("key")
            })
        
        return {"files": simplified_files, "count": len(simplified_files)}
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}


@mcp.tool()
async def upload_file_to_domino_project(
    user_name: str, 
    project_name: str, 
    file_path: str,
    file_content: str
) -> Dict[str, Any]:
    """
    Uploads a file to a Domino project. Works with DFS (non-git) projects.
    Use this to sync local file changes to a Domino project.

    Args:
        user_name (str): The username of the project owner (e.g., 'etan_lightstone')
        project_name (str): The name of the Domino project (e.g., 'diabetes_dfs_proj')
        file_path (str): The path where the file should be saved in the project (e.g., 'scripts/train.py')
        file_content (str): The content of the file to upload

    Returns:
        Dict containing upload result with 'path', 'size', 'key' on success,
        or 'error' if the operation failed.
    """
    # Get the project ID first
    project_id = _get_project_id(user_name, project_name)
    if not project_id:
        return {"error": f"Project '{project_name}' not found for user '{user_name}'"}
    
    # Upload endpoint
    url = f"{_get_domino_host()}/v4/projects/{project_id}/commits/head/files/{file_path}"
    
    # Prepare multipart form data
    headers = _get_auth_headers()
    files_data = {'upfile': (file_path.split('/')[-1], file_content, 'text/plain')}
    
    try:
        response = requests.post(url, headers=headers, files=files_data)
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "path": result.get("path"),
            "size": result.get("size"),
            "key": result.get("key"),
            "lastModified": result.get("lastModified")
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}


@mcp.tool()
async def download_file_from_domino_project(
    user_name: str, 
    project_name: str, 
    file_path: str
) -> Dict[str, Any]:
    """
    Downloads a file's content from a Domino project. Works with DFS (non-git) projects.
    Use this to get the latest version of a file from a Domino project.
    
    IMPORTANT: This function remembers the file version you downloaded. When you later
    use smart_sync_file to upload changes, it will detect if someone else modified
    the file in the meantime.

    Args:
        user_name (str): The username of the project owner (e.g., 'etan_lightstone')
        project_name (str): The name of the Domino project (e.g., 'diabetes_dfs_proj')
        file_path (str): The path of the file to download (e.g., 'scripts/train.py')

    Returns:
        Dict containing 'content' with the file content on success,
        plus 'key' which is the version identifier for conflict detection,
        or 'error' if the operation failed.
    """
    headers = {
        **_get_auth_headers(),
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }
    
    # Use editCode endpoint to get file content
    url = f"{_get_domino_host()}/v4/files/editCode"
    params = {
        "ownerUsername": user_name,
        "projectName": project_name,
        "pathString": file_path
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        # The content might be in different fields depending on file type
        content = result.get("content")
        if content is None:
            content = result.get("codeContent", "")
        
        # Get the file's key for version tracking
        remote_info = _get_remote_file_info(user_name, project_name, file_path)
        file_key = remote_info.get("key") if remote_info else None
        
        # Cache this version for conflict detection in smart_sync_file
        if file_key:
            cache_key = (user_name, project_name, file_path)
            _file_version_cache[cache_key] = {"key": file_key, "content": content}
        
        return {
            "success": True,
            "path": file_path,
            "content": content,
            "key": file_key,
            "commitId": result.get("currentCommitId")
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}


@mcp.tool()
async def sync_local_file_to_domino(
    user_name: str,
    project_name: str,
    local_file_path: str,
    domino_file_path: str | None = None
) -> Dict[str, Any]:
    """
    Reads a local file and uploads it to a Domino project. Works with DFS (non-git) projects.
    This is a convenience function that combines reading a local file and uploading it.

    Args:
        user_name (str): The username of the project owner (e.g., 'etan_lightstone')
        project_name (str): The name of the Domino project (e.g., 'diabetes_dfs_proj')
        local_file_path (str): The absolute path to the local file to upload
        domino_file_path (str, optional): The path in Domino where the file should be saved.
                                          If not provided, uses the filename from local_file_path.

    Returns:
        Dict containing upload result on success, or 'error' if the operation failed.
    """
    # Read the local file
    try:
        with open(local_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return {"error": f"Local file not found: {local_file_path}"}
    except Exception as e:
        return {"error": f"Failed to read local file: {e}"}
    
    # Determine the destination path
    if domino_file_path is None:
        domino_file_path = os.path.basename(local_file_path)
    
    # Upload to Domino
    return await upload_file_to_domino_project(
        user_name=user_name,
        project_name=project_name,
        file_path=domino_file_path,
        file_content=content
    )


@mcp.tool()
async def smart_sync_file(
    user_name: str,
    project_name: str,
    file_path: str,
    content: str,
    force_overwrite: bool = False
) -> Dict[str, Any]:
    """
    Intelligently syncs a file to a Domino project with conflict detection. Only use this for non-git projects (dfs based).
    
    This is the RECOMMENDED way to upload files when working with shared projects.
    It automatically detects if someone else modified the file since you last 
    downloaded it, and returns conflict information instead of blindly overwriting.
    
    Workflow:
    1. If you previously downloaded this file (via download_file_from_domino_project),
       we remember its version. Before uploading, we check if the remote changed.
    2. If remote changed → returns conflict with both versions so you can decide
    3. If remote unchanged → uploads your changes
    4. If file is new → uploads directly
    
    Args:
        user_name (str): The username of the project owner
        project_name (str): The name of the Domino project  
        file_path (str): The path where the file should be saved
        content (str): The new content to upload
        force_overwrite (bool): If True, skip conflict check and overwrite regardless.
                               Use this when you intentionally want to replace remote changes.

    Returns:
        On success: {"success": True, "action": "uploaded/created", "key": "..."}
        On conflict: {
            "conflict": True,
            "message": "Remote file changed since you last downloaded it",
            "your_content": "...",
            "remote_content": "...", 
            "remote_key": "...",
            "your_base_key": "...",
            "suggestion": "Review both versions and decide which to keep, or merge them"
        }
    """
    cache_key = (user_name, project_name, file_path)
    cached_version = _file_version_cache.get(cache_key)
    
    # Check current remote state
    remote_info = _get_remote_file_info(user_name, project_name, file_path)
    
    # Case 1: File doesn't exist remotely - just create it
    if remote_info is None:
        result = await upload_file_to_domino_project(user_name, project_name, file_path, content)
        if result.get("success"):
            # Update cache with new version
            _file_version_cache[cache_key] = {"key": result.get("key"), "content": content}
            return {
                "success": True,
                "action": "created",
                "message": f"Created new file: {file_path}",
                "key": result.get("key"),
                "size": result.get("size")
            }
        return result
    
    # Case 2: File exists but we haven't downloaded it before (no cached version)
    if cached_version is None and not force_overwrite:
        # Download the remote content to show the user what's there
        remote_result = await download_file_from_domino_project(user_name, project_name, file_path)
        remote_content = remote_result.get("content", "")
        
        # If content is identical, just upload (idempotent)
        if remote_content == content:
            _file_version_cache[cache_key] = {"key": remote_info["key"], "content": content}
            return {
                "success": True,
                "action": "no_change",
                "message": "File content identical to remote, no upload needed",
                "key": remote_info["key"]
            }
        
        return {
            "conflict": True,
            "message": f"File '{file_path}' already exists on Domino with different content. Download it first to establish a baseline, or use force_overwrite=True.",
            "remote_content": remote_content,
            "remote_key": remote_info["key"],
            "your_content": content,
            "suggestion": "Call download_file_from_domino_project first to see the remote version, then decide how to proceed"
        }
    
    # Case 3: We have a cached version - check if remote changed
    if cached_version and not force_overwrite:
        if remote_info["key"] != cached_version["key"]:
            # Remote changed! Fetch the new remote content
            remote_result = await download_file_from_domino_project(user_name, project_name, file_path)
            remote_content = remote_result.get("content", "")
            
            return {
                "conflict": True,
                "message": f"Remote file changed since you last downloaded it!",
                "your_base_key": cached_version["key"],
                "remote_key": remote_info["key"],
                "your_content": content,
                "remote_content": remote_content,
                "original_content": cached_version.get("content", ""),
                "suggestion": "Someone modified this file. Review the remote changes, merge if needed, then use force_overwrite=True to upload your final version."
            }
    
    # Case 4: Safe to upload (remote unchanged or force_overwrite)
    result = await upload_file_to_domino_project(user_name, project_name, file_path, content)
    if result.get("success"):
        # Update cache with new version
        _file_version_cache[cache_key] = {"key": result.get("key"), "content": content}
        action = "force_overwritten" if force_overwrite else "uploaded"
        return {
            "success": True,
            "action": action,
            "message": f"Successfully {action} {file_path}",
            "key": result.get("key"),
            "size": result.get("size")
        }
    return result


# async def main():
#     
#     print("making domino API call")
#     #result = await run_domino_job(user_name='etan_lightstone', project_name='diabetes-predict', run_command='python test.py', title='test run')
#     print(result)


if __name__ == "__main__":
    # Initialize and run the server using stdio transport
    mcp.run(transport='stdio') 
    #asyncio.run(main())