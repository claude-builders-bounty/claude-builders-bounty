# Claude Builders Bounty Board 🤖

This repository contains tools, hooks, and skills designed for Claude Code users.

---

## Solutions Included

### 1. Structured Changelog Generator ($50 Bounty)
A Python tool that automatically crawls your git commits since the last tag and groups them into `Added`, `Fixed`, `Removed`, and `Changed` categories in a clean `CHANGELOG.md` standard.

#### Installation & Usage
1. Make sure Python is installed.
2. In your Git repository, run:
   ```bash
   bash changelog.sh
   ```

---

### 2. Destructive Bash Blocker Hook ($100 Bounty)
A `PreToolUse` hook that intercepts and blocks dangerous commands (e.g. `rm -rf`, force pushes, unsafe SQL drops/deletes) in Claude Code, logging the attempts to `blocked.log`.

#### Installation
Run the install script:
```bash
bash install.sh
```

---

## Rules
- Tasks must be related to Claude Code or AI tooling.
- Quality over speed.

*MIT License*
