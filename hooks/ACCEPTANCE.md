# Acceptance checklist — Bounty #3 ($100)

- [x] Claude Code hooks format (`~/.claude/hooks/`)
- [x] Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log` (timestamp, reason, project, command)
- [x] Clear stderr message to Claude on block
- [x] Safe commands pass (ls, git status, DELETE with WHERE, chained commands)
- [x] Install in 1 command: `bash hooks/install.sh` + `settings.sample.json`
- [x] Tests: `python hooks/test_hook.py` (7 groups incl. e2e log)

/opire try — PR ready for merge.
