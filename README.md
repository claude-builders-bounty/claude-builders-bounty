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
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

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

---

## Issue #3: destructive-command guard

`hooks/block_destructive_commands.py` is a dependency-free Python PreToolUse
hook for Claude Code's `Bash` tool. It inspects the tool's JSON input without
executing the proposed command. It is intended to prevent accidental destructive
operations, not to provide a security sandbox for hostile shell programs.

### Install (two commands)

From this repository, on macOS or Linux with Python 3.9 or later:

```sh
python3 -m unittest discover -s tests -v
python3 install.py
```

The installer copies the hook to `~/.claude/hooks/` and registers a `Bash`
`PreToolUse` command in `~/.claude/settings.json`. Existing settings and hooks
are preserved. Existing settings are backed up before an update; running the
installer again with the same Python executable does not duplicate the entry.
No packages are installed and no network requests are made. Reopen Claude Code
after installation so the new hook configuration is loaded.

### Policy

The guard blocks these literal operations:

- `rm` with both recursive and force options, including combined, separate, and
  long options. A `--` terminator keeps filename arguments from becoming flags.
- Forced `git push`, including `-f`, `--force`, `--force-with-lease`, and explicit
  `+` refspecs. `--force-with-lease` is included deliberately because it still
  replaces remote history; `--force-if-includes` alone is allowed.
- SQL `DROP TABLE`, `DROP TEMPORARY TABLE`, and `TRUNCATE` statements, and
  `DELETE FROM` without a WHERE clause belonging to that DELETE. A WHERE inside
  a string, comment, or nested query does not count.

SQL inspection covers literal input to `sqlite3`, `duckdb`, `psql -c` /
`--command`, and `mysql` / `mariadb -e` / `--execute`, including literal
here-documents, here-strings, direct echo pipelines, and printf pipelines whose
SQL statement is present in a single argument.
Bare SQL statements are also checked. SQL quoted strings and identifiers are
distinguished from keywords; MySQL hash comments and PostgreSQL dollar-quoted
strings are handled. This is a limited keyword/depth inspection, not a full SQL
parser or a guarantee that a filtered deletion is safe.

Ordinary commands, non-forced pushes, read queries, filtered deletions, shell
comments, and echo/printf documentation strings pass without output or logging.
The guard recognizes common literal shell wrappers, compound command separators,
redirections, literal shell `-c` arguments, and command substitutions.

### Decisions and audit log

For `PreToolUse`, allowed commands exit with status **0**. Blocked commands exit
with status **2** and explain the reason on stderr. Stdout stays empty. Other
tools/events are ignored. Malformed Bash input, unterminated quoting, excessive
nesting, and inputs over 1 MiB are refused conservatively.

Each refusal appends one JSON line to `~/.claude/hooks/blocked.log` containing
`timestamp` (UTC), `command`, `project_path`, and `reason`. JSON escaping prevents
embedded newlines from forging records. New audit directories are private and
the log uses mode `0600`; appends are locked. Log symlinks and non-regular files
are rejected. If logging fails, the command remains blocked and stderr reports
the audit failure. Invalid input is represented by a fixed placeholder when no
command can be safely extracted.

The audit records contain the requested command verbatim, which may include
sensitive arguments. Keep this file private and do not include it in a PR.

### Scope and limitations

This guard does **not** evaluate variables, aliases, shell functions, `eval`,
external scripts, SQL loaded from files, generated/encoded SQL (including printf
formats assembling a statement across arguments), arbitrary
interpreters, or indirect data pipelines. It does not implement the entire Bash
or SQL grammar, and it cannot stop someone who intentionally encodes or hides an
operation. Keep normal tool permissions and human review in place. Only the
specified destructive patterns are covered; this is not an allowlist of safe
commands. A WHERE clause can still select every row.

Tests use temporary HOME directories and pass command strings as JSON data to
the hook. They never execute those strings or modify your real Claude settings.
The source archive contains no existing application or test suite; these are
new regression tests for the hook and installer. The local validation covers
the stdin/exit-code contract, not an interactive Claude Code session.

The offline implementation scope is recorded in
[`docs/ISSUE_3_REQUIREMENTS.md`](docs/ISSUE_3_REQUIREMENTS.md).
