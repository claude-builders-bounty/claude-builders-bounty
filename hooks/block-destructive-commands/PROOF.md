# Bounty #3 — Verification

## Run tests

From the repository root:

```bash
npm test
# or: make ci-validate
```

Or from this directory:

```bash
make ci-validate
# equivalent: bash tests/run-ci-checks.sh
```

## Expected output

```
Ran 104 tests in ...s
OK
Ran 6 delivery verification tests — OK
Ran 21 tests — OK
OK: peer review acceptance tests passed
OK: all CI validation checks passed
```

## Branch scope

`git diff main...HEAD` must include only hook-related paths (no `internal/exporter/*`
or other unrelated files). Peer-review acceptance test
`test_branch_diff_scoped_to_hook_only` enforces this.

## Hands-on verification (2026-06-16, fleet engineer)

Branch: `feat/issue-3-destructive-command-hook-v2` (PR #2556)

Removed re-introduced stray `feat: mkdocs export` commit (`internal/exporter/*`)
that broke `test_branch_diff_scoped_to_hook_only` and delivery scope checks.

## Hands-on verification (2026-06-16, hands-on takeover)

Removed stray fleet commit `ac58c06` that re-added `node_modules/*` (55k+ lines)
to `main...HEAD`, breaking `test_branch_diff_scoped_to_hook_only` and
`test_npm_test_entry_point_runs_green`. Reset to hook-only diff (`d1e32df` base);
all 104 unittest + 6 delivery + 21 peer-review checks green.

```bash
cd /workspace/claude-builders-bounty/claude-builders-bounty
git checkout feat/issue-3-destructive-command-hook-v2
npm test                    # 104 unittest + 6 delivery + 21 peer-review + attribution checks
make ci-validate            # same as npm test
```

CLI spot-checks:

```bash
# blocks destructive command with official schema
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' \
  | python3 hooks/block-destructive-commands/pre-tool-use.py
# -> {"hookSpecificOutput":{...,"permissionDecision":"deny",...}}

# allows safe commands (exit 0, no stdout)
echo '{"tool_name":"Bash","tool_input":{"command":"git status"},"cwd":"/tmp"}' \
  | python3 hooks/block-destructive-commands/pre-tool-use.py
```

Peer-review fix: `log_blocked_attempt()` sanitizes command and project_path via
`sanitize_log_field()` (newlines, backslashes, Unicode line separators, DEL/control chars).

Fork CI re-runs on push after this verification commit.
PR status: MERGEABLE/CLEAN against `main`.

## Acceptance criteria

- [x] PreToolUse hook in Claude Code format (`~/.claude/hooks/`)
- [x] Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log` (timestamp, sanitized command, project path)
- [x] Clear denial message via official `hookSpecificOutput` schema
- [x] Safe commands pass through unchanged
- [x] README with 2-command install (`git clone` + `install.sh`)
