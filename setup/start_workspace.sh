#!/bin/bash
# start_workspace.sh — Domino pre-run script for Claude Code
# Handles installation, per-user persistence, and plugin discovery.
# Run once automatically at workspace start.
#
# Security: OAuth credentials (~/.claude/.credentials.json) are scrubbed
# on each cold start to prevent token leakage via shared /mnt/artifacts.
# Preferences (~/.claude.json) are safe to persist — they contain no secrets.

set -e

echo "=== Claude Code Workspace Setup ==="

# ── 1. Install Claude Code if not present ──────────────────────────────
if ! command -v claude &> /dev/null; then
    echo "[!] Claude Code not found. Installing via native installer..."
    curl -fsSL https://claude.ai/install.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "[✓] Claude Code version: $(claude --version 2>/dev/null || echo 'installed')"

# ── 2. Determine per-user persistent storage ───────────────────────────
# /mnt/artifacts persists across cold starts but is shared by all users
# in a project, so we isolate by DOMINO_USER_NAME.

if [ -n "$DOMINO_USER_NAME" ]; then
    PERSIST_USER="$DOMINO_USER_NAME"
else
    PERSIST_USER="$USER"
    echo "[!] DOMINO_USER_NAME not set, falling back to: $PERSIST_USER"
fi

PERSIST_DIR="/mnt/artifacts/.claude-users/${PERSIST_USER}/.claude"

mkdir -p "$PERSIST_DIR"

echo "[i] Persistent storage: $PERSIST_DIR"

# ── 3. Symlink ~/.claude to persistent storage ─────────────────────────
HOME_CLAUDE="$HOME/.claude"

# If ~/.claude exists as a real directory, migrate contents
if [ -d "$HOME_CLAUDE" ] && [ ! -L "$HOME_CLAUDE" ]; then
    echo "[i] Migrating existing ~/.claude to persistent storage..."
    cp -r "$HOME_CLAUDE/"* "$PERSIST_DIR/" 2>/dev/null || true
    rm -rf "$HOME_CLAUDE"
fi

# Remove broken symlink if present
[ -L "$HOME_CLAUDE" ] && [ ! -e "$HOME_CLAUDE" ] && rm -f "$HOME_CLAUDE"

# Create symlink
if [ ! -L "$HOME_CLAUDE" ]; then
    ln -s "$PERSIST_DIR" "$HOME_CLAUDE"
    echo "[✓] ~/.claude symlinked to $PERSIST_DIR"
else
    echo "[✓] ~/.claude persistence already configured"
fi

# ── 4. Force fresh authentication ─────────────────────────────────────
# OAuth credentials live in ~/.claude/.credentials.json (inside the
# persisted directory). Remove them on each cold start so tokens from
# one user can't be read by another user sharing /mnt/artifacts.
rm -f "$HOME/.claude/.credentials.json" 2>/dev/null || true
rm -f "$HOME/.claude/backups/.claude.json.backup."* 2>/dev/null || true
echo "[✓] Cleared OAuth credentials — you will need to re-authenticate"

# ── 5. Persist ~/.claude.json (preferences, not secrets) ──────────────
# This file stores theme, editor mode, tool trust, MCP configs, etc.
# It does NOT contain OAuth tokens, so it's safe in shared storage.
PERSIST_JSON="/mnt/artifacts/.claude-users/${PERSIST_USER}/.claude.json"
HOME_JSON="$HOME/.claude.json"

if [ ! -f "$PERSIST_JSON" ]; then
    if [ -f "$HOME_JSON" ] && [ ! -L "$HOME_JSON" ]; then
        echo "[i] Migrating existing ~/.claude.json to persistent storage..."
        cp "$HOME_JSON" "$PERSIST_JSON"
    else
        echo '{}' > "$PERSIST_JSON"
    fi
fi

# Remove existing file or broken symlink
rm -f "$HOME_JSON" 2>/dev/null || true

if [ ! -L "$HOME_JSON" ]; then
    ln -s "$PERSIST_JSON" "$HOME_JSON"
    echo "[✓] ~/.claude.json symlinked to $PERSIST_JSON"
else
    echo "[✓] ~/.claude.json persistence already configured"
fi

# ── 6. Register plugins (skills, commands, agents) ─────────────────────
PLUGIN_DIR="/mnt/code/domino-claude-plugin"

mv $PLUGIN_DIR/skills ~/.claude/
mv $PLUGIN_DIR/commands ~/.claude/
mv $PLUGIN_DIR/agents ~/.claude/
mv $PLUGIN_DIR/output-styles ~/.claude/

echo "[✓] Registered $(ls /mnt/code/.claude/skills/ 2>/dev/null | wc -l) skills, $(ls /mnt/code/.claude/commands/ 2>/dev/null | wc -l) commands, $(ls /mnt/code/.claude/agents/ 2>/dev/null | wc -l) agents"
# Cleanup
mv $PLUGIN_DIR/.* ~/
mv $PLUGIN_DIR/* ~/
rm -rf $PLUGIN_DIR
echo "=== Claude Code setup complete ==="
