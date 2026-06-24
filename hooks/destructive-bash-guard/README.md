# Destructive Bash Guard - Claude Code Pre-Tool-Use Hook

A safety net that intercepts dangerous bash commands **before Claude executes them**.

## What it blocks

| Category | Patterns |
|---|---|
| Filesystem | rm -rf /, rm -rf ~, rm -rf *, mkfs, dd of=/dev/, chmod 777, fork bombs |
| Database | DROP TABLE/DATABASE/SCHEMA, TRUNCATE, DELETE FROM without WHERE |
| Git | git push --force to main/master/prod, git reset --hard, git clean -fd |
| Network | curl \| sh, wget \| bash, curl \| python |
| System | shutdown, reboot, halt, init 0, wipefs, shred /dev/ |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/destructive-bash-guard/block_destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.py
python3 hooks/destructive-bash-guard/install.py
# Restart Claude Code to activate
```

## How it works

When Claude tries to run a Bash tool call, this hook reads the JSON payload from stdin, runs every pattern regex (case-insensitive, multiline) against the command, and either returns `permissionDecision: deny` with a structured explanation (if matched) or `permissionDecision: allow` (if not).

Multi-line SQL is handled correctly. DELETE FROM x; (no WHERE) is detected via statement-level scan. Each block is appended to `~/.claude/hooks/blocked.log`.

## Override

```bash
DESTRUCTIVE_GUARD_OVERRIDE=1 claude
```

Bypasses the guard for the entire session. Logged as warning.

## Customization

Edit `patterns.yaml` to add or remove patterns without touching code:

```yaml
- name: my-custom-rule
  regex: '\bsome-dangerous-command\b'
  severity: high
  description: My custom rule description
```

## Testing

```bash
python3 -m unittest tests.test_block_destructive -v
```

## Compatibility

Python 3.9+ | Claude Code hooks protocol (PreToolUse) | macOS, Linux, WSL

## Files

```
hooks/destructive-bash-guard/
├── block_destructive.py        # main hook
├── patterns.yaml               # configurable patterns
├── install.py                  # 1-command installer
├── README.md                   # this file
└── tests/
    ├── __init__.py
    └── test_block_destructive.py
```

## License

MIT
