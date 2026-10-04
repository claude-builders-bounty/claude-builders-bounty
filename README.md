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
3. Submit a PR — the board advertises automatic payment on merge, but the
   current Opire funding, maintainer acceptance, and payout state must be
   verified before treating any reward as payable.

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

## Destructive-command guard hook

This repository includes `hooks/destructive_command_guard.py`, a dependency-free
Claude Code `PreToolUse` hook for the bounty in [issue #3](../../issues/3). It
denies `rm -rf`, forced or mirrored Git pushes (including forced refspecs set
through `git -c remote.<name>.push=+...`), `DROP TABLE`, `TRUNCATE`, and `DELETE FROM`
without a `WHERE` clause. It also inspects `$(...)`, backticks, and process
substitutions for nested destructive commands, while leaving single-quoted and
escaped examples untouched; shell nesting deeper than 32 levels is denied
conservatively. It also follows common command prefixes (`time`, `nice`,
`timeout`, and `stdbuf`) and inspects direct commands run through `eval`,
`find -exec`, and `xargs`. This is a best-effort guard, not a complete shell
parser or security sandbox; do not treat an allowed command as proof that
arbitrary dynamic code is safe. Every denial is appended as one JSON line to
`~/.claude/hooks/blocked.log`, including the UTC timestamp, a best-effort
redacted and length-limited attempted command, and project path. Common secret
flags, credential assignments, bearer values, credential-bearing URLs, and
recognizable API-key formats are redacted before logging. Ordinary commands
(including scoped SQL deletes) remain untouched. The denial response contains
a clear explanation for Claude and a safer, scoped alternative (for example,
previewing files before removal, pushing a new branch, or adding a reviewed SQL
predicate). Invalid hook input is denied and logged with an explicit placeholder
instead of being silently treated as safe. The automated tests exercise real
hook subprocesses with representative PreToolUse JSON. An isolated live
Claude Code session using Claude Pro also verified two actual Bash tool calls:
a harmless `printf` command ran successfully, and `git push --force --dry-run`
was denied before execution and logged. That smoke test used no repository or
remote and changed no global Claude settings; it validates only those two
cases, not every shell pattern or hosted CI.
On POSIX systems the log is restricted to owner read/write permissions, and
the hook refuses to follow a symlink at the log path; other platforms use their
normal filesystem ACLs.

From the repository root, install it and merge its `PreToolUse` matcher into
your existing Claude settings with one command:

```bash
python3 hooks/install.py
```

On Windows, use the Python launcher instead:

```powershell
py -3 hooks/install.py
```

The installer copies the hook to `~/.claude/hooks/`, preserves unrelated
settings, and writes a `Bash` matcher using the Python interpreter that ran
the installer. That makes the generated command invocable on Windows as well
as POSIX shells. If that Python installation moves, rerun the same one-command
installer to refresh the matcher.

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
