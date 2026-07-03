# Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://code.claude.com/docs/en/hooks) `PreToolUse` hook that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm -r -f` / `rm --recursive --force` | Recursive force delete (any flag order) |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | SQL schema destruction |
| `git reset --hard` | Discards uncommitted and untracked local changes |
| `git push --force` / `git push -f` / `git push +<ref>` / `git -c push.force=true push` | Rewrites remote history (allows `--force-with-lease` and `-c push.force=false`) |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |
| `dd ... of=/dev/*` | Raw disk overwrite |
| `> /dev/sd*` / `>> /dev/nvme*` | Shell redirect to raw block device |
| `mkfs` / `mkfs.ext4` | Filesystem format (destroys data) |
| `wipefs` | Disk signature wipe |
| `:(){ :|:& };:` fork bomb | Process exhaustion attack |
| `curl ... \| bash` / `wget ... \| sh` | Remote script execution |

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

The installer copies the hook to `~/.claude/hooks/` and merges the `PreToolUse` entry into `~/.claude/settings.json` without overwriting your other hooks.

To remove the hook:

```bash
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh --uninstall
```

Uses the official Claude Code `hookSpecificOutput` schema (`permissionDecision: deny`) — not the legacy `decision: block` format.

## How it works

1. Intercepts every `Bash` tool call via the `PreToolUse` hook
2. Splits chained commands on `;`, `&&`, and `||`, then checks each segment independently
3. Decodes bash `$'...'` ANSI-C quoting in `sh -c` / `bash -c` payloads before pattern matching
4. **Blocks** matching commands and returns a clear denial message to Claude
5. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path (command and path are sanitized before write to prevent log injection)
6. **Allows** safe commands to pass through unchanged

## Hook protocol

Claude Code sends JSON on stdin. When a command is blocked, the hook prints the official denial schema:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Recursive force delete (rm -rf) blocked. Run this command directly in your terminal if you truly need it."
  }
}
```

Safe commands produce no stdout and exit `0`.

## Operator trade-offs

**Silent failures on malformed input or internal errors.** The hook intentionally
fails open: malformed JSON, empty stdin, non-`Bash` tool calls, and unexpected
internal errors exit `0` with no stdout so legitimate commands are never blocked
because the hook crashed. Operators who prefer fail-closed behavior must wrap or
replace the hook — this implementation prioritizes availability over strict
enforcement when the hook itself cannot parse input reliably.

**Unicode invisible-character normalization.** Before pattern matching, commands
are normalized to collapse zero-width format characters (Unicode Cf/Mn), null
bytes, and filler glyphs (U+115F/U+1160 Hangul choseong/jungseong, U+3164 Hangul
filler, U+FFA0 halfwidth, U+2800 braille blank) that can split tokens like `rm`
and `-rf` without changing visible text.

**Regex and substring matching limits.** Detection inspects command text with
regex and substring rules; it does not execute or fully parse shell syntax.
`rm -rf` is only blocked when `rm` is executed (including after `|` pipeline
stages and inside `sh -c` wrappers), not when the text appears in `echo`,
`grep`, or similar display/search utilities. Obfuscated or indirect commands
can still evade blocking. For example, `x=rm; $x -rf /` stores the destructive
utility in a variable and invokes it later, so the segment may not match `rm -rf`
patterns. Treat this hook as a safety net for common destructive patterns, not a
complete shell sandbox.

## Blocked log

```bash
cat ~/.claude/hooks/blocked.log
```

Example entry:

```
[2026-06-06T12:34:56Z] Command: rm -rf /tmp/build | Project: /home/user/project
```

Newlines, backslashes, Unicode line separators, and other control characters in the
command or project path are escaped or replaced before writing so malicious payloads
cannot forge extra log lines.

## Tests

From this directory:

```bash
make test
# or: python3 -m unittest discover -s tests -v
# 155+ regression tests (unit + bounty + delivery + peer-review acceptance)
```

From the repository root:

```bash
npm test
# or: make ci-validate
# or: make -C hooks/block-destructive-commands test
```

The CI runner executes all regression tests, peer-review acceptance checks, and
attribution guards used by GitHub Actions.

## License

MIT
