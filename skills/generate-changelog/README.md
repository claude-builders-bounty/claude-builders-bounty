# generate-changelog

A Claude Code skill that turns a project's git history into a structured
`CHANGELOG.md` (Added / Fixed / Changed / Removed), no API calls, no model
tokens per commit.

## Install in 3 steps

```bash
# 1. copy the skill into your Claude Code skills directory
mkdir -p ~/.claude/skills && cp -r skills/generate-changelog ~/.claude/skills/

# 2. from any git repo, preview what would be written
bash ~/.claude/skills/generate-changelog/scripts/changelog.sh --dry-run

# 3. write the release block
bash ~/.claude/skills/generate-changelog/scripts/changelog.sh --version v1.4.0
```

That is the whole setup — `git` and `bash` are the only requirements.

## What it does

- Range defaults to `git describe --tags --abbrev=0 .. HEAD`; falls back to the
  root commit when the repo has no tags.
- Classifies commits by Conventional Commits type, then by keywords
  (`add`/`fix`/`remove`), then defaults to **Changed**.
- Skips version bumps and `Merge pull request ...` noise.
- Emits Keep-a-Changelog headings: `## [version] - date` + `### Added` etc.
- Links each entry to its PR (`(#123)`) and its commit, built from
  `git remote get-url origin`.
- Prepends the new block above older entries instead of clobbering the file.

## Requirements met

| Criterion | Where |
|---|---|
| Works via `/generate-changelog` or `bash changelog.sh` | `SKILL.md` workflow + `scripts/changelog.sh` |
| Fetches commits since the last git tag | `--from` default = `git describe --tags --abbrev=0` |
| Categorises into Added / Fixed / Changed / Removed | `categorisation` section of the script |
| Outputs a properly formatted CHANGELOG.md | Keep-a-Changelog headings, prepended |
| Tested on a real GitHub repo | `examples/CHANGELOG.sample.md` (chalk/chalk, `v5.6.2..v6.0.1`) |

## Sample output

Real run, no hand editing:

```bash
$ git clone https://github.com/chalk/chalk && cd chalk
$ bash scripts/changelog.sh --from v5.6.2 --to v6.0.1 --version v6.0.1 --stdout
```

Result: [`examples/CHANGELOG.sample.md`](examples/CHANGELOG.sample.md).

```markdown
## [v6.0.1] - 2026-11-26

### Added

- Add extended underline styles and underline colors ([#689](.../pull/689), [`4c304dd`](.../commit/4c304dd))

### Fixed

- Downsample `ansi256()` and `bgAnsi256()` to 16 colors at level 1 ([#687](.../pull/687), [`ff549c5`](...))
```

## Why not `git-cliff` / `conventional-changelog`?

Both are good; both need Node or Rust toolchains and a config file. This is a
single 200-line bash file you can read in one sitting and run in CI images that
only have `git`. Different trade-off, not a better one.

## Unattended use

```bash
bash scripts/changelog.sh --version "$(git describe --tags --abbrev=0)" --stdout >> "$GITHUB_STEP_SUMMARY"
```

Commits with no conventional prefix cannot be classified perfectly — the
keyword fallback is deliberate, and `--dry-run` exists so a human can correct the
section before the file is touched.

MIT, same as the repository.
