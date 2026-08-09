# Destructive Bash Guard for Claude Code

This is a dependency-free `PreToolUse` hook that blocks a focused set of high-risk Bash commands before Claude Code runs them:

- recursive-and-forced deletes such as `rm -rf` and `rm -r -f`;
- forced Git pushes such as `git push --force`, `--force-with-lease`, and `-f`;
- `DROP TABLE` and `TRUNCATE` SQL statements; and
- `DELETE FROM` statements that do not contain a `WHERE` clause.

Blocked attempts are written to `~/.claude/hooks/blocked.log` with an ISO-8601 UTC timestamp, the project path, the matched rule, and the original command. Safe commands continue through Claude Code's normal permission flow.

The matcher also handles common `sudo`, `env`, and absolute-path prefixes.

## Install

From the repository root, run one command:

```bash
python3 hooks/install.py
```

The installer copies the hook to `~/.claude/hooks/`, merges a `PreToolUse`/`Bash` entry into `~/.claude/settings.json` without removing existing settings, and makes a one-time backup at `settings.json.before-destructive-hook`. Restart Claude Code or open `/hooks` to verify it.

The manual configuration equivalent is in [`settings.example.json`](settings.example.json).

## Hook contract

Claude Code sends a JSON `PreToolUse` event on stdin. The hook returns a structured `hookSpecificOutput` denial on stdout and exits `0`, matching the current Claude Code hook contract. It fails open for malformed input or non-Bash events so unrelated tools are not interrupted.

Run the tests with:

```bash
python3 -m unittest discover -s hooks -p 'test_*.py'
```
