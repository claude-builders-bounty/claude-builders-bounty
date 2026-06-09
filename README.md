 # Claude Code Destructive Bash Guard

This repository contains a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

Run `bash install.sh`.

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and registers it in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and privileged variants
- `git push --force`, `git push -f`, and `--force-with-lease`
- `git reset --hard`
- `git clean -fd`
- SQL `DROP DATABASE`, `DROP SCHEMA`, `DROP TABLE`, and `TRUNCATE`
- SQL `DELETE FROM table` without a `WHERE` clause
- raw disk writes such as `dd ... of=/dev/sda`
- filesystem formatting commands such as `mkfs.ext4 /dev/...`
- broad recursive `chmod -R 777 /`

## How It Works

The hook reads the Claude Code hook payload from stdin and inspects `tool_input.command`.

When a destructive command is detected, it returns a Claude Code denial response with `hookSpecificOutput.hookEventName` set to `PreToolUse` and `hookSpecificOutput.permissionDecision` set to `deny`.

Safe commands exit without output, allowing Claude Code to continue normally. Blocked commands are appended to `~/.claude/hooks/blocked.log` as JSONL.

## Test

Run `python3 -m unittest discover -s tests`.

A command like `rm -rf /tmp/build` should return a denial response.

A command like `npm test` should produce no output and be allowed.

A command like `DELETE FROM users;` should return a denial response and be logged.
