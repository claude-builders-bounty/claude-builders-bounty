# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Solved |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Destructive Bash Command Hook (#3)

A zero-dependency `PreToolUse` hook for Claude Code that prevents accidental or unintended system destruction by intercepting dangerous bash commands before execution.

### Quick Installation (<= 2 commands)

Automated 1-command installer (cross-platform):
```bash
python install.py
```

Or manual 2-command installation:
```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive.py ~/.claude/hooks/
cp .claude/settings.json ~/.claude/settings.json
```

### What It Blocks

| Category | Blocked Patterns | Safe Allowed Counterparts |
|---|---|---|
| **File Deletions** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` (any target) | `rm file.txt`, `rm -f temp.log`, `rm -r build/` (without force) |
| **SQL Destruction** | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA` | `SELECT * FROM users;`, table alter/create queries |
| **Git Force Push** | `git push --force`, `git push -f`, `--force-with-lease`, `+ref` | `git push`, `git push origin feat`, `git status`, `git commit` |
| **SQL Truncation** | `TRUNCATE TABLE`, `TRUNCATE <table>` | Coreutils file truncate (`truncate -s 0 file.log`) |
| **Unbounded Delete** | `DELETE FROM <table>` (without a `WHERE` clause) | `DELETE FROM users WHERE id = 1;` |
| **Raw Disk Formats** | `mkfs`, `mkfs.ext4`, `dd if=... of=/dev/sd*` | `dd if=/dev/zero of=test.bin` (writing to files) |
| **Fork Bombs / DoS** | `:(){ :\|:& };:`, `while true; do ... & done` | Normal while/for loops |
| **System State** | `shutdown`, `reboot`, `poweroff`, `init 0` | Build and dev servers |
| **Root Permissions** | `chmod -R 777 /`, `chown -R ... /` | Local project permissions (`chmod +x run.sh`) |

### Audit Logging

All blocked operations are automatically appended to `~/.claude/hooks/blocked.log`:
```text
[2026-09-03T13:25:00Z] [CWD: /home/user/project] [RULE: rm_rf] BLOCKED: rm -rf / | REASON: Destructive file deletion: 'rm -rf' detected in 'rm -rf /'
```
The log path can be overridden via `CLAUDE_HOOK_BLOCKED_LOG` or `CLAUDE_BLOCKED_LOG_PATH` environment variables.

### Testing & Verification

Run the native test suite (100% standard library, zero external pip dependencies):
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Run the standalone reproduction and verification harness:
```bash
python tests/reproduce_issue_3.py
```

Direct CLI checking mode:
```bash
python .claude/hooks/block_destructive.py --check "rm -rf /"       # Exit code 2 (BLOCKED)
python .claude/hooks/block_destructive.py --check "git status"     # Exit code 0 (ALLOWED)
```

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
