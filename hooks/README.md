# Domino Plugin Hooks

This directory contains example Claude Code hooks for Domino workflows. Hooks are shell commands that run automatically in response to Claude Code events.

## How to Use

Copy the example hooks below to your `.claude/hooks.json` file to enable them.

## Example Hooks

### Validate app.sh Before Save

Validates that `app.sh` binds to the correct host for Domino:

```json
{
  "hooks": [
    {
      "type": "PreToolUse",
      "tool": "Write",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -q 'app.sh$'; then if ! echo \"$CLAUDE_CONTENT\" | grep -q '0.0.0.0'; then echo 'Warning: app.sh should bind to 0.0.0.0, not localhost'; fi; fi"
    }
  ]
}
```

### Check Python Syntax

Validates Python syntax after editing:

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "tool": "Edit",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -qE '\\.py$'; then python3 -m py_compile \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
    }
  ]
}
```

### Validate Dockerfile

Validates Dockerfile syntax (requires hadolint):

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "tool": "Edit",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -qi 'dockerfile'; then hadolint \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
    }
  ]
}
```

### Format Python on Save

Auto-format Python files with black:

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "tool": "Write",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -qE '\\.py$'; then black --quiet \"$CLAUDE_FILE_PATH\" 2>/dev/null || true; fi"
    }
  ]
}
```

## Combined Example

Here's a complete `.claude/hooks.json` with multiple hooks:

```json
{
  "hooks": [
    {
      "type": "PreToolUse",
      "tool": "Write",
      "description": "Validate app.sh binds to 0.0.0.0",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -q 'app.sh$'; then if ! echo \"$CLAUDE_CONTENT\" | grep -q '0.0.0.0'; then echo 'Warning: app.sh should bind to 0.0.0.0 for Domino'; fi; fi"
    },
    {
      "type": "PostToolUse",
      "tool": "Edit",
      "description": "Check Python syntax",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -qE '\\.py$'; then python3 -m py_compile \"$CLAUDE_FILE_PATH\" 2>&1 || true; fi"
    },
    {
      "type": "PostToolUse",
      "tool": "Write",
      "description": "Format Python files",
      "command": "if echo \"$CLAUDE_FILE_PATH\" | grep -qE '\\.py$'; then black --quiet \"$CLAUDE_FILE_PATH\" 2>/dev/null || true; fi"
    }
  ]
}
```

## Hook Types

| Type | Description |
|------|-------------|
| `PreToolUse` | Runs before a tool executes |
| `PostToolUse` | Runs after a tool completes |
| `UserPromptSubmit` | Runs when user submits a prompt |

## Environment Variables

Available in hooks:
- `CLAUDE_FILE_PATH` - Path to the file being operated on
- `CLAUDE_CONTENT` - Content being written (for Write tool)
- `CLAUDE_TOOL_NAME` - Name of the tool being executed

## Installation

1. Create `.claude/hooks.json` in your project or home directory
2. Add the desired hooks from the examples above
3. Restart Claude Code to load the hooks

## Notes

- Hooks run synchronously and can block Claude Code
- Use `|| true` to prevent hook failures from blocking operations
- Test hooks carefully before enabling in production workflows
