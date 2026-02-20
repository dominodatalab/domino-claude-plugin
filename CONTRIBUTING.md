# Contributing to Domino Data Lab Plugin

Thank you for your interest in contributing to the Domino Data Lab Plugin for Claude Code!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch

```bash
git clone https://github.com/YOUR_USERNAME/domino-data-lab-plugin.git
cd domino-data-lab-plugin
git checkout -b feature/your-feature-name
```

## Development Setup

Test the plugin locally with Claude Code:

```bash
claude --plugin-dir /path/to/domino-data-lab-plugin
```

## Plugin Structure

```
domino-data-lab-plugin/
├── .claude-plugin/plugin.json   # Plugin manifest (required)
├── skills/                      # Agent skills
├── commands/                    # Slash commands
├── agents/                      # Subagents
├── output-styles/               # Custom output styles
├── templates/                   # Code templates
└── hooks/                       # Example hooks
```

## Contribution Guidelines

### Adding a New Skill

1. Create a new directory under `skills/`
2. Add a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: domino-your-skill
description: Brief description of what this skill does. Include trigger keywords.
---

# Your Skill Name

## Description
Detailed description of the skill...
```

3. Add the skill to `plugin.json`
4. Keep SKILL.md under 500 lines; use supporting files for details

### Adding a New Command

1. Create a markdown file under `commands/`
2. Include description in frontmatter:

```yaml
---
description: What this command does
---

# /command-name

Usage and documentation...
```

3. Add the command to `plugin.json`

### Adding a New Agent

1. Create a markdown file under `agents/`
2. Include full frontmatter:

```yaml
---
name: domino-agent-name
description: When to use this agent. Use PROACTIVELY when...
tools: Read, Edit, Write, Bash, Grep, Glob
model: inherit
skills: skill1, skill2
---
```

3. Add the agent to `plugin.json`

## Code Style

- Use consistent YAML frontmatter format
- Include code examples with proper language tags
- Use tables for reference documentation
- Keep descriptions actionable and specific

## Testing Changes

Before submitting:

1. Verify all referenced files exist
2. Test skills trigger correctly
3. Verify commands work as documented
4. Check for broken internal links

```bash
# Verify file structure
find skills -name "SKILL.md" | wc -l  # Should match plugin.json count

# Check for broken links
grep -r "\](\./" --include="*.md" | head -20
```

## Pull Request Process

1. Update the README if adding new features
2. Add your changes to CHANGELOG (if it exists)
3. Ensure all tests pass
4. Request review from maintainers

## Reporting Issues

Please include:
- Claude Code version
- Plugin version
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue for bugs or feature requests
- See [Domino Documentation](https://docs.dominodatalab.com/) for platform questions
