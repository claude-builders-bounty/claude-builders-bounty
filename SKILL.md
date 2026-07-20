---
name: block-destructive-commands
description: "Pre-tool-use hook that blocks dangerous bash commands in Claude Code."
tags: [security, hook, safety, claude-code]
---

# Block Destructive Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands.

## What it blocks

- Filesystem: `rm -rf`, `chmod 777`, recursive ownership
- SQL: `DROP TABLE`, `TRUNCATE`, `DELETE` without `WHERE`
- Git: `push --force`, `reset --hard`, `clean -f`
- System: fork bombs, shutdown/reboot
- Supply chain: `curl | bash`

## Installation

```bash
curl -sSL https://raw.githubusercontent.com/.../hook.py | python3 - --install
```

## Features

- Safe path allowlist (node_modules, /tmp still work)
- 25 built-in self-tests
- Configurable via guard.config.json
- Proper uninstall command
