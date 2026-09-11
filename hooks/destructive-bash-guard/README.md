# Claude Code Destructive Bash Guard Hook

A pre-tool-use security hook for Claude Code that intercepts and blocks dangerous bash operations before execution.

Part of the **[Claude Builders Bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)** ($100 USD via Opire).

---

## Features & Acceptance Criteria

- ✅ **Native Claude Code Hook**: Follows `~/.claude/hooks/pre-tool-use` standard.
- ✅ **Intercepts High-Risk Operations**:
  - `rm -rf` / `rm -fr` / `--recursive --force`
  - `DROP TABLE` (case-insensitive SQL)
  - `git push --force` / `-f` / `--force-with-lease`
  - `TRUNCATE` / `TRUNCATE TABLE`
  - `DELETE FROM` without a `WHERE` clause
- ✅ **Audit Logging**: Appends every blocked attempt with an ISO-8601 timestamp, command, and project directory to `~/.claude/hooks/blocked.log`.
- ✅ **Context-Aware Explanation**: Displays a clear, actionable message to Claude explaining why the action was rejected.
- ✅ **Zero Disruption for Safe Commands**: Passes through normal commands (`git push`, `npm test`, `DELETE FROM ... WHERE ...`, `rm file.txt`) with zero overhead.
- ✅ **Quick Installation**: Installs in 2 commands or fewer.

---

## Installation (2 Commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && cd claude-builders-bounty
bash hooks/destructive-bash-guard/install.sh
```

*(Or direct single-line curl install)*:
```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/destructive-bash-guard/install.sh | bash
```

---

## Testing & Verification

Run the comprehensive unit test suite:

```bash
python3 -m unittest test_guard.py
```

### Manual Testing

Test an allowed command:
```bash
~/.claude/hooks/pre-tool-use "git status"
# Exits with 0 (allowed)
```

Test a blocked command:
```bash
~/.claude/hooks/pre-tool-use "rm -rf /tmp/test"
# Intercepted! Displays safety warning and exits with 1
```

Inspect the audit log:
```bash
cat ~/.claude/hooks/blocked.log
```

---

## Opire Payout Configuration

- **Issue**: [claude-builders-bounty/issues/3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)
- **Reward**: $100 USD (Opire)
- **Target Beneficiary Wallet**: `0x4B4031bd3B334e010E6ecE66d14DEa59eB34122a` (Base Mainnet / EVM)
