# Claude Code PreToolUse destructive command guard

This is a protocol-correct Claude Code `PreToolUse` hook for Bash commands. It blocks destructive shell/SQL patterns before execution, logs every blocked attempt to `~/.claude/hooks/blocked.log`, and returns a clear `permissionDecision: "deny"` message to Claude.

## Two-command install

Run these commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp bounties/issue-3-hook/claude_pre_tool_use_guard.py ~/.claude/hooks/claude_pre_tool_use_guard.py && chmod +x ~/.claude/hooks/claude_pre_tool_use_guard.py
python3 ~/.claude/hooks/claude_pre_tool_use_guard.py --install
```

The installer registers this hook in `~/.claude/settings.json` as a `PreToolUse` hook for the `Bash` matcher while preserving existing settings.

## What it blocks

Required bounty patterns:

- `rm -rf` equivalents: `rm -rf target`, `rm -fr target`, `sudo rm --recursive --force target`
- SQL `DROP TABLE`
- `git push --force`, `git push -f`, `--force-with-lease`, and forced `+refspec` pushes
- SQL `TRUNCATE`
- SQL `DELETE FROM` without a `WHERE` clause

## What it allows

The hook is intentionally conservative so normal Bash commands are not interrupted:

- harmless commands such as `ls`, `npm test`, `git status`, `git push`
- `DELETE FROM users WHERE id = 1`
- text/search commands that merely mention dangerous SQL, such as `grep "DROP TABLE" docs/*.md`
- non-Bash tool calls

## Claude Code protocol behavior

For blocked Bash commands the hook prints JSON to stdout and exits successfully:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked recursive forced deletion (`rm -rf` / equivalent)..."
  }
}
```

This uses the current Claude Code `PreToolUse` decision-control format instead of deprecated top-level `decision` / `reason` fields.

## Blocked log format

Every blocked attempt appends one JSONL entry to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-05-16T04:00:00+00:00","command":"rm -rf build","project_path":"/path/to/project","rule":"rm-rf","reason":"Blocked recursive forced deletion..."}
```

The log includes the required timestamp, attempted command, and project path, plus the matched rule and reason for auditability.

## Local verification

```bash
python3 -m unittest discover -s bounties/issue-3-hook/tests
python3 bounties/issue-3-hook/claude_pre_tool_use_guard.py --check 'rm -rf build'
python3 bounties/issue-3-hook/claude_pre_tool_use_guard.py --check 'git status'
```
