# Pre-Tool-Use Safety Hook

A configurable pre-tool-use hook that blocks destructive bash commands before
they execute. Designed for LLM tool-use pipelines (GitHub Copilot, LangChain,
OpenAI function-calling, etc.).

## What It Catches

| Category | Blocked Examples | Allowed Examples |
|---|---|---|
| **Filesystem** | `rm -rf /`, `rm -rf /etc` | `rm -rf node_modules`, `rm file.txt` |
| **SQL** | `DROP TABLE users`, `DROP DATABASE prod` | `DROP TABLE IF EXISTS test_users` |
| **Git** | `git push --force origin main` | `git push origin main`, force-push to feature branches |
| **Permissions** | `chmod 777 /etc`, `chmod -R 777 /usr` | `chmod 755 ./deploy.sh` |
| **Disk** | `mkfs.ext4 /dev/sda1`, `dd of=/dev/sda` | `dd if=a.img of=b.img`, `mkfs /dev/loop0` |
| **System** | `shutdown`, `reboot`, `halt`, `init 0` | -- |
| **Processes** | `kill -9 1`, `killall sshd`, `kill -9 -1` | `kill 12345`, `kill -9 54321` |
| **Other** | Fork bombs, `curl \| sh`, Python `shutil.rmtree('/')` | Normal curl, pip install |

## How It Works

```
Command String
     |
     v
+---------------+
| Normalise     |  Collapse whitespace, decode hex/octal escapes,
|               |  extract subcommands from pipes/chains/subshells
+-------+-------+
        v
+---------------+
| Rule Match    |  Each rule is a regex + severity (critical/high/medium/low)
|               |  that maps to a base score (100/70/40/20)
+-------+-------+
        v
+---------------+
| Allowlist     |  Per-rule allowlist regexes suppress false positives
|               |  (e.g., test databases, project-relative paths)
+-------+-------+
        v
+---------------+
| Compound      |  Contextual modifiers (sudo, --no-preserve-root, output
| Modifiers     |  suppression) add extra points when any rule has fired
+-------+-------+
        v
+---------------+
| Verdict       |  total_score >= threshold (default 100) -> BLOCK
+---------------+
```

Multiple risk factors **compound**: a medium-severity rule (40 pts) won't block
alone, but combined with `sudo` (+20) and output suppression (+10) it gets
closer. Two medium rules together will block.

## Quick Start

### Requirements

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- pytest (for tests only)

### Installation

```bash
git clone <repo-url>
cd bounties/safety-hook
pip install pyyaml pytest
```

### Usage

#### As a CLI

```bash
# Evaluate a single command
python3 safety-hook.py "rm -rf /"
# [BLOCK] score=100/100
#   command: 'rm -rf /'
#   W [CRITICAL] +100  Recursive forced deletion of filesystem root (/)

python3 safety-hook.py "ls -la"
# [ALLOW] score=0/100
#   command: 'ls -la'
```

#### JSON output

```bash
python3 safety-hook.py -j "rm -rf /"
# {"verdict": "BLOCK", "blocked": true, "score": 100, ...}
```

#### JSON input (tool-call payload)

```bash
echo '{"tool":"bash","command":"rm -rf /"}' | python3 safety-hook.py --json
```

#### As a Python library

```python
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location("safety_hook", "safety-hook.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

hook = mod.SafetyHook()

result = hook.evaluate("rm -rf /")
if result.blocked:
    print(result.report())

result = hook.evaluate("ls -la")
assert not result.blocked  # Safe command
```

#### Integration with tool-use pipelines

```python
def pre_tool_hook(tool_name: str, tool_input: dict) -> dict:
    """Drop-in hook for LLM tool-use middleware."""
    hook = SafetyHook()
    result = hook.evaluate_tool_call({"tool": tool_name, **tool_input})
    if result.blocked:
        return {
            "error": f"Command blocked: {result.report(verbose=False)}",
            "details": result.to_dict(),
        }
    return None  # Allow execution
```

### Running Tests

```bash
python3 -m pytest test_safety_hook.py -v
```

The test suite includes **60+ test cases** across these categories:

| Category | Tests |
|---|---|
| Blocked commands | 35 (rm, SQL, git, chmod, disk, shutdown, kill, fork bomb, chained, Python) |
| Allowed commands | 18 (safe rm, safe SQL, normal git, safe chmod, everyday commands) |
| Normalisation | 4 (whitespace, hex decode, subcommands, subshells) |
| Compound scoring | 4 (sudo, --no-preserve-root, output suppression, modifier isolation) |
| Result API | 4 (verdict, to_dict, report) |
| CLI integration | 4 (blocked, allowed, JSON output, JSON input) |
| Edge cases | 6 (empty, whitespace, comments, multiline, long, unicode) |

## Configuration

Edit `hook-config.yaml` to customise rules:

```yaml
# Raise/lower the blocking threshold (default: 100)
threshold: 100

# Adjust severity scores
severity_scores:
  critical: 100
  high: 70
  medium: 40
  low: 20

# Add custom rules
rules:
  - id: my_custom_rule
    pattern: '\bmy-dangerous-command\b'
    severity: critical
    message: "Custom dangerous command detected"
    allowlist:
      - '--safe-mode'

# Add compound modifiers
compound_modifiers:
  - pattern: '\bsudo\b'
    score: 20
    message: "Elevated privileges (sudo)"
```

### Key Configuration Concepts

- **threshold**: Total score needed to block. Lower = more aggressive.
- **severity_scores**: Map severity names to point values.
- **rules**: Each rule has a regex `pattern`, `severity`, human-readable `message`,
  and optional `allowlist` of regexes that suppress the rule.
- **compound_modifiers**: Extra score added when contextual patterns appear alongside
  *any* triggered rule. They don't fire on their own.

## Architecture Decisions

1. **Scoring over binary**: A scoring system allows nuanced decisions. A `medium`
   rule alone won't block, but `medium + sudo + output suppression` will --
   matching real-world threat profiles.

2. **Allowlists over blocklists alone**: Every rule can have per-rule allowlists
   to reduce false positives without weakening protection.

3. **Normalisation layer**: Commands are normalised before matching to defeat
   simple obfuscation (hex escapes, whitespace padding, quote splitting).

4. **Subcommand extraction**: Chained commands (`&&`, `||`, `;`, `|`) and
   subshells (`$(...)`, backticks) are individually evaluated.

5. **Compound modifiers**: Contextual signals like `sudo` or `--no-preserve-root`
   amplify risk only when a base rule has already fired -- they never block
   innocent commands.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Command ALLOWED |
| `1` | Command BLOCKED |
| `2` | Usage error |

## License

MIT
