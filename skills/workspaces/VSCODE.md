# VS Code Workspaces in Domino

## Overview

Domino provides VS Code as a workspace option, offering a full-featured code editor with extensions, debugging, and terminal access.

## Features

- Full VS Code editor in browser
- Extension support
- Integrated terminal
- Git integration
- Debugging support
- GitHub Copilot support

## Starting a VS Code Workspace

### Via UI
1. Go to **Workspaces** > **Launch Workspace**
2. Select **VS Code**
3. Choose hardware tier and environment
4. Click **Launch**

### Via Python SDK
```python
from domino import Domino

domino = Domino("project-owner/project-name")

workspace = domino.workspace_start(
    workspace_type="VSCode",
    hardware_tier_name="medium",
    environment_id="your-environment-id"
)
```

## VS Code Extensions

### Pre-installed Extensions
Domino VS Code workspaces typically include:
- Python extension
- Jupyter extension
- Git extension

### Installing Additional Extensions
1. Open Extensions panel (`Ctrl+Shift+X`)
2. Search for extension
3. Click **Install**

Note: Extensions installed in a session may not persist. For permanent extensions, configure in the Domino Environment.

## GitHub Copilot Integration

### Setup
1. Ensure GitHub Copilot is enabled in your organization
2. Sign in with GitHub in VS Code
3. Authorize Copilot

### Usage
```python
# Start typing and Copilot suggests completions
def calculate_mean(numbers):
    # Copilot will suggest implementation
```

## Remote SSH Access

Connect to Domino workspaces from your local VS Code:

### Prerequisites
- Domino 6.1+
- VS Code Remote SSH extension locally
- SSH access enabled on workspace

### Setup
1. Install **Remote - SSH** extension in local VS Code
2. Get SSH connection string from Domino workspace
3. Add to SSH config:
```
Host domino-workspace
    HostName workspace-hostname.domino.tech
    User domino
    IdentityFile ~/.ssh/domino_key
```

4. Connect: `Remote-SSH: Connect to Host` > `domino-workspace`

### Benefits
- Use local VS Code with remote compute
- All local extensions available
- Faster response than browser-based VS Code

## Working with Python

### Select Interpreter
1. `Ctrl+Shift+P` > **Python: Select Interpreter**
2. Choose the correct Python environment

### Run Code
- `F5`: Run with debugger
- `Ctrl+F5`: Run without debugger
- Right-click > **Run Python File**

### Debug
```python
# Add breakpoints by clicking line numbers
# Press F5 to start debugging
# Use debug toolbar to step through code
```

## Working with Jupyter Notebooks

VS Code supports Jupyter notebooks natively:

1. Create new notebook: `Ctrl+Shift+P` > **Create: New Jupyter Notebook**
2. Or open existing `.ipynb` file
3. Run cells with `Shift+Enter`

## Terminal Access

Open integrated terminal:
- `Ctrl+`` (backtick)
- Or **Terminal** > **New Terminal**

```bash
# Run commands
pip install pandas
python train.py
git status
```

## File Management

### Project Files
- Located in `/mnt/` directory
- Auto-synced with Domino project
- Use Explorer panel to navigate

### Save and Sync
- Files auto-save (configurable)
- Click **Sync** in Domino UI to push to project
- Or use Git for version control

## Settings

### User Settings
`Ctrl+,` to open settings

Common settings:
```json
{
    "editor.fontSize": 14,
    "editor.tabSize": 4,
    "python.linting.enabled": true,
    "python.formatting.provider": "black",
    "files.autoSave": "afterDelay"
}
```

### Workspace Settings
Create `.vscode/settings.json` in project:
```json
{
    "python.defaultInterpreterPath": "/opt/conda/bin/python",
    "python.terminal.activateEnvironment": true
}
```

## Git Integration

### Initialize Repository
```bash
git init
git remote add origin https://github.com/user/repo.git
```

### Source Control Panel
- View changes in Source Control panel
- Stage, commit, push from UI
- View diffs inline

### Git Commands
`Ctrl+Shift+G` to open Source Control

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Command Palette | `Ctrl+Shift+P` |
| Quick Open File | `Ctrl+P` |
| Find in Files | `Ctrl+Shift+F` |
| Toggle Terminal | `Ctrl+`` |
| Toggle Sidebar | `Ctrl+B` |
| Go to Definition | `F12` |
| Find References | `Shift+F12` |

## Troubleshooting

### VS Code Slow
- Check hardware tier resources
- Close unused extensions
- Reduce number of open files

### Extensions Not Working
- Check extension compatibility with VS Code version
- Verify dependencies are installed
- Check extension logs

### Can't Connect Remote SSH
- Verify SSH is enabled on workspace
- Check firewall rules
- Verify SSH key permissions

## Documentation Reference
- [Configure native Workspaces](https://docs.dominodatalab.com/en/latest/user_guide/4e7f25/configure-native-workspaces/)
- [Use Workspaces](https://docs.dominodatalab.com/en/latest/user_guide/867b72/use-workspaces/)
