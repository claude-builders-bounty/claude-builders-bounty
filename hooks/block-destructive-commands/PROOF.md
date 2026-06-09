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
Ran 95 tests in ...s
OK
Ran 5 delivery verification tests — OK
Ran 19 tests — OK
OK: peer review acceptance tests passed
OK: all CI validation checks passed
```

## Branch scope

`git diff main...HEAD` must include only hook-related paths (no `internal/exporter/*`
or other unrelated files). Peer-review acceptance test
`test_branch_diff_scoped_to_hook_only` enforces this.

## Hands-on verification (2026-06-09)

Branch: `feat/issue-3-destructive-command-hook-v2` (PR #2556)

```bash
cd /workspace/claude-builders-bounty/claude-builders-bounty
git checkout feat/issue-3-destructive-command-hook-v2
npm test                    # 95 unittest + 5 delivery + 18 peer-review + attribution checks
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

Fork CI: green on `dca70d6` (test-block-destructive-commands workflow).
PR status: MERGEABLE/CLEAN against `main`.

## Acceptance criteria

- [x] PreToolUse hook in Claude Code format (`~/.claude/hooks/`)
- [x] Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log` (timestamp, command, project path)
- [x] Clear denial message via official `hookSpecificOutput` schema
- [x] Safe commands pass through unchanged
- [x] README with 2-command install (`git clone` + `install.sh`)
