# beamo-changelog

Structured `CHANGELOG.md` generator from git history (since the last tag).

Relates to [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) · Beamo LLC · beamo@beamosupport.com

## Setup (3 steps)

1. Copy this folder into your project (or clone this PR branch).
2. From a git repo: `bash beamo-changelog/changelog.sh`
3. Open the generated `CHANGELOG.md`.

**Optional Claude Code command:** copy `.claude/commands/generate-changelog.md` into your project's `.claude/commands/` (or copy `.claude/skills/generate-changelog/` into `~/.claude/skills/`), then run `/generate-changelog`.

## What it does

- Reads commits **since the latest git tag** (or full history if untagged)
- Auto-categorizes into **Added / Fixed / Changed / Removed**
  - Understands Conventional Commits (`feat:`, `fix:`, `chore:`, …)
  - Falls back to keyword heuristics (`add`, `fix`, `remove`, `update`, …)
- Writes a Keep-a-Changelog-style `CHANGELOG.md`

## Usage

```bash
bash changelog.sh                  # write/update CHANGELOG.md
bash changelog.sh --stdout         # print only
bash changelog.sh --replace        # overwrite instead of prepend
bash changelog.sh --from v1.0.0    # custom start ref
bash changelog.sh -o notes.md      # custom output path
```

## Sample

See [`samples/CHANGELOG.express.md`](samples/CHANGELOG.express.md) — generated against [expressjs/express](https://github.com/expressjs/express) between tags `v5.0.0` and `v5.1.0`.

## Tests

```bash
bash tests/run-tests.sh
```

## License

MIT (same as parent repository)
