# Bounty #3: Safety Hook — Pre-Tool-Use Dangerous Command Blocker

**Status:** Reference Implementation  
**Bounty:** $100 USD  
**Category:** Claude Code Hooks / Pre-Tool-Use

---

## Overview

This safety hook intercepts every `bash` tool-use invocation inside Claude Code,
scans the command against a configurable blocklist of dangerous patterns, and
either **blocks**, **warns**, or **allows** the command depending on the
configured severity level.

---

## Quick Start

```bash
# 1. Clone or copy the hook into your project
cp safety-hook.sh /path/to/your/project/
cp config.example.yaml /path/to/your/project/.claude/config.yaml

# 2. Register the hook in Claude Code settings
mkdir -p .claude
cat >> .claude/settings.json << 'EOF'
{
  "hooks": {
    "pre-tool-use": {
      "script": "${PROJECT_DIR}/safety-hook.sh",
      "timeout": 10000
    }
  }
}
EOF

# 3. Make the hook executable
chmod +x safety-hook.sh

# 4. Start using Claude Code — dangerous commands are now blocked
```

---

## How It Works

### Protocol

Claude Code invokes the hook script and passes the tool-use request as a JSON
object on **stdin**:

```json
{
  "type": "tool_use",
  "name": "bash",
  "input": { "command": "rm -rf /" },
  "tool_use_id": "call_abc123"
}
```

The hook returns a JSON verdict on **stdout**:

```json
// Allow
{ "isBlocked": false }

// Block
{ "isBlocked": true, "message": "rm -rf / would destroy the system — blocked." }
```

If `isBlocked` is `true`, Claude Code halts and presents the message to the
user.

### Pipeline

```
stdin JSON → Parse command → Normalize → Allowlist check
                                              ↓
                                         (match?) ──yes──→ Allow
                                              ↓
                                           Scoped rules
                                              ↓
                                         (match?) ──yes──→ Check severity
                                              ↓
                                        Global rules
                                              ↓
                                         (match?) ──yes──→ Check severity
                                              ↓
                                          No match → Allow
```

### Severity Levels

| Level                    | Behavior                                                      |
|--------------------------|---------------------------------------------------------------|
| `block`                  | Always blocked. No override possible.                         |
| `warn`                   | Blocked unless one of: `--dangerous` flag in command,         |
|                          | `SAFETY_HOOK_CONFIRM=true` env var, or interactive confirm.   |
| `allow_with_confirmation`| Allowed after interactive confirmation (same mechanisms as    |
|                          | `warn`).                                                      |
| `allow`                  | Always allowed. Used in allowlists and relaxed scoped rules.  |

### Confirmation Mechanisms (for `warn` / `allow_with_confirmation`)

1. **`--dangerous` flag** — Append `--dangerous` anywhere in the command to
   auto-allow: `rm -rf /some/important/path --dangerous`

2. **`SAFETY_HOOK_CONFIRM`** — Set the environment variable:
   `export SAFETY_HOOK_CONFIRM=true`
   This disables all warnings for the session.

3. **Interactive prompt** — When running in a TTY, the hook displays a prompt
   with options to allow once (`y`), allow for the session (`Y`), inspect the
   full command (`i`), or reject (`n`).

---

## Configuration

### File: `.claude/config.yaml`

```yaml
safety_hook:
  default_level: warn
  log_file: "~/.claude/safety-hook.log"

rules:
  - pattern: "rm\\s+-rf\\s+/"
    level: block
    message: "..."

allowlist:
  - "rm -rf node_modules"
  - "docker system prune -f"

scoped_rules:
  - directory: "/path/to/production"
    rules:
      - pattern: "git push --force"
        level: block
```

All rules, allowlists, and scoped rules are **optional**. The hook ships with
sensible defaults for 14 dangerous patterns.

### Environment Variables

| Variable               | Default                              | Description                       |
|------------------------|--------------------------------------|-----------------------------------|
| `SAFETY_HOOK_CONFIG`   | `<script-dir>/config.yaml`           | Path to YAML config               |
| `SAFETY_HOOK_LOG`      | `~/.claude/safety-hook.log`          | Path to audit log                 |
| `SAFETY_HOOK_CONFIRM`  | _(unset)_                            | `true`/`1` to auto-confirm warns  |
| `SAFETY_HOOK_DEBUG`    | _(unset)_                            | `true` for verbose debug logging  |

---

## Default Blocked Patterns

| # | Pattern                    | Severity | Description                               |
|---|----------------------------|----------|-------------------------------------------|
| 1 | `rm -rf /`                 | block    | Root filesystem destruction               |
| 2 | `rm -rf ~`                 | block    | Home directory destruction                |
| 3 | `dd if=`                   | block    | Disk overwrite                            |
| 4 | `:(){ :\|:& };:`           | block    | Fork bomb                                 |
| 5 | `> /dev/sda`               | block    | Direct disk write                         |
| 6 | `mkfs.`                    | block    | Filesystem format                         |
| 7 | `chmod -R 777 /`           | block    | World-writable root                       |
| 8 | `sudo rm -rf /`            | block    | Root-level system destruction             |
| 9 | `sudo rm -rf ~`            | block    | Root-level home destruction               |
| 10| `curl ... \| bash`         | warn     | Remote code execution risk                |
| 11| `wget ... \| sh`           | warn     | Remote code execution risk                |
| 12| `git push --force`         | warn     | History rewrite                           |
| 13| `drop table`               | warn     | Database destruction                      |
| 14| `delete from` (no WHERE)   | warn     | Mass row deletion                         |

---

## Default Allowlist

- `npm run build -- --clean`
- `rm -rf node_modules`
- `rm -rf .next`
- `rm -rf dist`
- `docker system prune -f`
- `npm run dev -- --clear`
- `cargo clean`

---

## Audit Log

All safety events are timestamped and written to `~/.claude/safety-hook.log`:

```
[2026-07-13T10:15:30+0000] [INFO ] Hook initialized
[2026-07-13T10:15:45+0000] [MATCH] Rule #7 matched: cmd='sudo rm -rf /tmp/foo' pattern='sudo\s+rm' level='block'
[2026-07-13T10:15:45+0000] [BLOCK] Blocked command: sudo rm -rf /tmp/foo
[2026-07-13T10:16:02+0000] [ALLOW_LIST] rm -rf node_modules allowed by allowlist
[2026-07-13T10:16:30+0000] [PASS] npm install passed with no matching rules
```

---

## Testing

```bash
# Verify the hook rejects dangerous commands
echo '{"name":"bash","input":{"command":"rm -rf /"}}' | bash safety-hook.sh
# → {"isBlocked":true,"message":"..."}

# Verify allowlist commands pass through
echo '{"name":"bash","input":{"command":"rm -rf node_modules"}}' | bash safety-hook.sh
# → {"isBlocked":false}

# Verify safe commands pass through
echo '{"name":"bash","input":{"command":"echo hello"}}' | bash safety-hook.sh
# → {"isBlocked":false}

# Verify --dangerous flag works
echo '{"name":"bash","input":{"command":"dd if=/dev/zero of=/tmp/test bs=1 count=1 --dangerous"}}' | bash safety-hook.sh
# → {"isBlocked":false}

# Verify non-bash tools pass through
echo '{"name":"read","input":{"filePath":"/etc/hosts"}}' | bash safety-hook.sh
# → {"isBlocked":false}
```

---

## Security Considerations

- The hook runs **before** the command executes; it cannot prevent race
  conditions where a malicious actor modifies the command between check and
  execution.
- YAML config files should be readable only by trusted users.
- The `--dangerous` flag and `SAFETY_HOOK_CONFIRM` env var are escape hatches
  intended for power users. In high-security environments, remove the escape
  hatches from the script.

---

## Dependencies

- **bash** ≥ 4.0 (for associative arrays)
- **jq** or **python3** (one of the two, for reliable JSON parsing)
- **yq** (optional, for full YAML support; hook includes a built-in fallback
  parser for common YAML patterns)

---

## License

MIT — See [LICENSE](../LICENSE) in the monorepo root.
