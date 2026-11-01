# Destructive-command guard for Claude Code

Standalone contribution for Claude Builders issue #3. Uses the Python standard library only.

## Install (from this directory)

```sh
python3 install.py
```

Requires Python 3.10+. Restart Claude Code afterward. The installer copies the hook to `~/.claude/hooks/`, merges a `Bash` `PreToolUse` entry into `~/.claude/settings.json`, and backs up existing settings/hook files. Review before installation. Existing unrelated permissions are preserved.

## Behavior

- Denies recursive+forced `rm`, including split flags and long flags.
- Denies forced git pushes, including `--force-with-lease`; leaves `--force-if-includes` alone.
- Checks DROP TABLE, TRUNCATE, and DELETE FROM without WHERE in each SQL statement (including common SQL CLI arguments).
- Appends a JSONL record with UTC timestamp, attempted command and hook input `cwd` to `~/.claude/hooks/blocked.log` (0600 on creation). Logs can contain sensitive command arguments; keep them private.
- Emits the current `hookSpecificOutput.permissionDecision: deny` protocol. Normal commands produce no decision and do not bypass Claude's normal permission checks. Non-Bash tools are ignored; malformed input exits 2.

## Test without third-party packages

```sh
python3 -m unittest -v
```

Tests invoke only the hook, never execute the dangerous strings. CLI/log tests use an isolated HOME. Set `HOOK_TEST_TMPDIR` to choose the parent temporary directory. The installer was separately exercised twice in an isolated HOME to verify idempotency, backups and preservation of unrelated settings.

## Limits

This is a pattern-based guard, **not a shell parser, SQL parser, sandbox or security boundary**. Shell expansions, encoded programs, dynamically assembled commands, aliases/functions, unusual interpreters and indirect execution can evade it. Some unusual commands can produce false positives. Only the documented literal/common-wrapper cases are tested. Standalone protocol tests are not an end-to-end live Claude Code session or maintainer acceptance.

## Sources and licensing

- Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
- Protocol: https://code.claude.com/docs/en/hooks
- Distributed under the repository's MIT license.
