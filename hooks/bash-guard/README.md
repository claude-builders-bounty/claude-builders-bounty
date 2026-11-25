# Bash guard for Claude Code

Requires Python 3.8+ and a POSIX-compatible shell for Claude Code command hooks. From a checkout, run `python3 hooks/bash-guard/install.py`, then restart Claude Code. The installer copies the hook into `~/.claude/hooks/` and merges a Bash matcher into `~/.claude/settings.json`. If you maintain that file in a dotfiles manager, review its diff.

The hook reads a single PreToolUse event on stdin. It denies recursive forced removal, forced Git pushes, and direct SQL statements that drop or truncate a table or delete rows without a top-level WHERE. It checks SQL arguments to common command-line clients and literal text piped to a client with echo or printf. Other inspected commands proceed with Claude Code's usual permission checks.

Each denial includes the reason and writes one JSON record to `~/.claude/hooks/blocked.log`. That local file contains original command text, timestamp and project path. Restrict access and rotate it according to your retention policy. The guard inspects command text. Underlying filesystem, database and Git server permissions still apply to scripts, generated inputs and other tools.

Run `python3 hooks/bash-guard/test_guard.py` in a checkout. The tests feed inert command strings through stdin and install to a temporary profile. [Claude Code hook reference](https://code.claude.com/docs/en/hooks#pretooluse)
