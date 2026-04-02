---
name: tmux-cli
description: CLI utility to communicate with other CLI Agents or Scripts in other tmux panes; use it only when user asks you to communicate with other CLI Agents or Scripts in other tmux panes.
tags:
  - byte-skill
---

# tmux-cli

## Instructions

使用 `${CLAUDE_PLUGIN_ROOT}` 变量引用插件根目录：

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/skills/tmux-cli/scripts tmux-cli <command>
```

## Key Commands

### Execute with Exit Code Detection

Use `tmux-cli execute` when you need to know if a shell command succeeded or failed:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/skills/tmux-cli/scripts tmux-cli execute "make test" --pane=2
# Returns JSON: {"output": "...", "exit_code": 0}

uv run --directory ${CLAUDE_PLUGIN_ROOT}/skills/tmux-cli/scripts tmux-cli execute "npm install" --pane=ops:1.3 --timeout=60
# Returns exit_code=0 on success, non-zero on failure, -1 on timeout
```

This is useful for:
- Running builds and knowing if they passed
- Running tests and detecting pass/fail
- Multi-step automation that should abort on failure

**Note**: `execute` is for shell commands only, not for agent-to-agent chat.
For communicating with another Claude Code instance, use `send` + `wait_idle` +
`capture` instead.

### Interactive Programs

When sending commands to programs that display interactive menus or take time
to render (e.g., selection prompts, fzf-like interfaces), disable Enter
verification to prevent extra keypresses:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/skills/tmux-cli/scripts tmux-cli send "interactive-command" --pane=2 --verify-enter=False
```