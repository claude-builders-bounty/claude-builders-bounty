# Destructive Command Guard for Claude Code 🛡️

A zero-dependency `pre-tool-use` hook for **Claude Code** that intercepts and blocks dangerous commands before execution.

---

## ⚡ Quick Install (2 Commands or Fewer)

Run this single command from this repository:

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

Or execute the provided installer:

```bash
./install.sh
```

---

## 🎯 Acceptance Criteria Compliance

| Criterion | Status | Implementation Details |
|---|---|---|
| **Claude Code Hook Format** | ✅ | Native `~/.claude/hooks/pre-tool-use` executable hook |
| **Blocks `rm -rf`** | ✅ | Catches `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` |
| **Blocks `DROP TABLE`** | ✅ | Case-insensitive detection across SQL CLI invocations |
| **Blocks `git push --force`** | ✅ | Blocks `--force`, `-f`, and `--force-with-lease` |
| **Blocks `TRUNCATE`** | ✅ | Blocks `TRUNCATE [TABLE] <name>` across all SQL variants |
| **Blocks unbounded `DELETE FROM`** | ✅ | Enforces presence of `WHERE` clause per SQL statement |
| **Audit Logging** | ✅ | Appends to `~/.claude/hooks/blocked.log` (UTC ISO timestamp, cwd, reason, cmd) |
| **Clear Claude Explanation** | ✅ | Detailed message to `stderr` with exit code `2` (aborts tool call) |
| **Zero Interference** | ✅ | Permits build/test tools, git commits, echo/print, and scoped SQL |
| **<= 2-Command Install** | ✅ | Single-line copy or `./install.sh` |

---

## 🔍 How It Works

Before executing any bash command requested by Claude Code, this hook evaluates the payload:

1. **Input Inspection**: Parses the JSON tool payload from `stdin` (`tool`, `tool_input.command`, `cwd`).
2. **Pipeline Decomposition**: Analyzes commands split by `;`, `&&`, `||`, and `|`.
3. **Safe Context Filter**: Automatically skips string literals inside harmless commands like `echo`, `printf`, or code comments.
4. **Enforcement & Feedback**:
   - If a destructive pattern is found:
     - Appends full audit trail to `~/.claude/hooks/blocked.log`.
     - Prints a detailed security block notice to `stderr`.
     - Exits with status `2` to halt execution.
   - If clean, exits with status `0` allowing normal command execution.

---

## 📝 Audit Log Format

Logged entries in `~/.claude/hooks/blocked.log` follow this structured format:

```text
[2026-10-01T04:48:00.000000+00:00] [BLOCKED] cwd=/workspace/repo | reason=Destructive recursive file deletion (rm -rf) | command=rm -rf /tmp/data
[2026-10-01T04:48:05.000000+00:00] [BLOCKED] cwd=/workspace/repo | reason=Destructive SQL operation (DROP TABLE) | command=DROP TABLE users;
```

---

## 🧪 Running Tests

The test suite validates both positive denials and false-positive avoidance:

```bash
python3 tests/test_guard.py
```

Output:
```text
Ran 8 tests in 0.002s

OK
```

---

## 💳 Bounty Payout Reference
- **GitHub Bounty**: Issue #3 ($100 USD)
- **Contributor**: `lam534410-hub`
- **Payout Rails**:
  - **PayPal (USD)**: `lamvukyo3001@gmail.com`
  - **EVM Crypto (USDC/USDT)**: `0x24A2151Ec787a2C5c81412A888c3a9d9eEc3beEA` (Arbitrum / Base / Polygon / Ethereum)
