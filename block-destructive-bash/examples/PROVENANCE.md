# Test Provenance

## Test suite

`bash test-hook.sh` — **22 assertions, all passing** (run 2026-10-14):

- **11 must-block** (exit 2): `rm -rf /`, `sudo rm -rf ./build`,
  `rm -fr node_modules`, `rm -r -f dist`, `rm --recursive --force cache`,
  `git push --force origin main`, `git push -f`, `DROP TABLE users`,
  `TRUNCATE TABLE sessions`, `DELETE FROM users` (no WHERE),
  `git reset --hard HEAD~5`
- **10 must-allow** (exit 0): `rm notes.txt`, `rm -r empty-dir`,
  `git push origin main`, `git push --force-with-lease origin main`,
  `DELETE FROM users WHERE id = 42`, `SELECT * FROM users`, `ls -la`,
  `echo hello`, `git commit -m 'wip'`
- **1 passthrough**: a non-Bash tool call (Edit) whose input contains
  `rm -rf /` passes untouched
- **Log schema**: every blocked attempt writes a valid JSON line with
  `ts` / `command` / `project` / `reason` fields

## Parser paths

Both JSON-parsing paths were exercised:

- **jq path** — default when jq is on PATH
- **python3 fallback** — verified with a minimal PATH excluding jq
  (`rm -rf /` blocked, `git push` allowed, log written correctly)

## Installer

`bash install.sh` was run against a sandboxed `HOME`:

1. Hook copied to `~/.claude/hooks/block-destructive-bash.sh`, made executable
2. `~/.claude/settings.json` created/merged with the `PreToolUse` entry
   (matcher `Bash`, command `bash ~/.claude/hooks/block-destructive-bash.sh`)
3. Re-run is idempotent ("already registered in settings.json — nothing to do")
4. Live probe through the installed path: `git push --force` blocked with
   rc=2, explanation on stderr, JSON line appended to `blocked.log`

## Design notes

- Flag detection unions all short-flag tokens, so `-rf`, `-fr`, and the
  separated `-r -f` are all caught
- `--force-with-lease` deliberately passes — it is the documented safe
  alternative to `--force`
- The scan is intentionally conservative: a compound command whose *other*
  tools carry r/f flags can false-positive, which errs on the side of
  blocking; the block message tells the user how to proceed
