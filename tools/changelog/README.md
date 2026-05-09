# generate-changelog

Turn `git log` since the last tag into a [Keep a Changelog]-formatted CHANGELOG.md
section, auto-categorized into **Added / Changed / Fixed / Removed** using
[Conventional Commits] prefixes plus verb-prefix heuristics for non-conventional
commits. Closes [#1](../../issues/1).

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Conventional Commits]: https://www.conventionalcommits.org/

```
tools/changelog/
├── README.md                      ← you are here
├── generate_changelog.py          ← single-file Python 3, stdlib only
├── changelog.sh                   ← thin bash wrapper (matches bounty's `bash changelog.sh`)
├── SKILL.md                       ← Claude Code skill (`/generate-changelog`)
├── samples/
│   └── sample-pallets-click.md    ← real run against pallets/click
└── tests/test_changelog.py        ← 16 unittest cases (no deps)
```

## Install (3 steps)

```bash
# 1. Drop the folder into your project (or any path on disk)
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/tools/changelog/generate_changelog.py -o tools/changelog/generate_changelog.py

# 2. (Optional) wire it as a Claude Code skill
mkdir -p .claude/skills && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/tools/changelog/SKILL.md -o .claude/skills/generate-changelog.md

# 3. Run
python tools/changelog/generate_changelog.py --version v1.2.0 --in-place
```

## Three ways to invoke

### CLI

```bash
# Default: print the diff since the last tag to stdout
python tools/changelog/generate_changelog.py

# Update CHANGELOG.md in place, prepending a new release section
python tools/changelog/generate_changelog.py --version v1.2.0 --in-place

# From a specific base ref
python tools/changelog/generate_changelog.py --since v1.1.0 --version v1.2.0

# Render commit hashes as clickable GitHub links
python tools/changelog/generate_changelog.py --repo-url https://github.com/owner/repo
```

### Bash wrapper

```bash
bash tools/changelog/changelog.sh --version v1.2.0 --in-place
```

The wrapper just delegates to the Python script — provided so the bounty's
`bash changelog.sh` invocation works literally.

### Claude Code skill (`SKILL.md`)

Drop `SKILL.md` into `.claude/skills/generate-changelog.md` in your project,
then ask Claude Code:

> "Generate the changelog for the next release."

Claude routes to the skill, which calls the script and shows you the new
section before any in-place writes.

## All flags

| Flag | Default | Description |
|---|---|---|
| `--repo PATH` | `.` | Project root (must be inside a git repo) |
| `--since REF` | last tag | Base ref (tag, branch, or sha). Falls through to "entire history" if no tag exists. |
| `--version LABEL` | `Unreleased` | Version label for the new section header |
| `--date YYYY-MM-DD` | today | Date for the new section header |
| `--output FILE` | stdout | Write to a file (use `-` for stdout) |
| `--in-place` | — | Update `CHANGELOG.md` in the repo, prepending the new section |
| `--repo-url URL` | — | GitHub URL so commit hashes render as clickable links |
| `--include-skipped` | false | Include `chore` / `docs` / `test` / `style` / `build` / `ci` commits as Changed |
| `--include-merges` | false | Include merge commits (default: skipped) |
| `--quiet` | — | Suppress stderr informational messages |

Exit codes: `0` wrote a section · `1` git error · `2` no commits since the base ref.

## Categorization rules

**Conventional Commits** map directly:

| Prefix | Bucket |
|---|---|
| `feat:` / `feat(scope):` | Added |
| `fix:` / `fix(scope):` | Fixed |
| `perf:` | Changed |
| `refactor:` | Changed |
| `revert:` | Removed |
| `deps:` | Changed |
| `chore:` / `docs:` / `style:` / `test:` / `build:` / `ci:` | _filtered_ (use `--include-skipped` to keep) |

**`!:` or `BREAKING CHANGE:` in body** flips the section into Changed (or
keeps it in Removed for `revert!:`) and adds a banner at the top of the
release: _"⚠️ This release contains breaking changes — review before
upgrading."_

**Non-conventional commits** are categorized by verb prefix on the subject:

| Subject starts with | Bucket |
|---|---|
| Add / Adds / Added / Implement / Introduce / Create / Support | Added |
| Fix / Fixes / Fixed / Resolve / Patch / Correct / Address | Fixed |
| Remove / Drop / Delete / Deprecate / Revert | Removed |
| Update / Improve / Refactor / Rename / Change / Replace / Migrate / Bump / Upgrade | Changed |
| _anything else_ | Changed (catch-all) |

**Merge commits** (`git log --no-merges`) are skipped by default.

## Idempotent in-place updates

`--in-place` does the right thing whether or not `CHANGELOG.md` exists:

- **No file** → creates one with the Keep-a-Changelog preamble + your new section.
- **Existing file** → finds the top-level `# Changelog` header, walks past
  any preamble paragraphs, and inserts your new section directly above the
  first existing `## [version]` block. Existing release history is
  preserved.

Re-running on the same range is safe — the new section is added once
per invocation; older sections stay untouched.

## Real sample

[`samples/sample-pallets-click.md`](samples/sample-pallets-click.md) was
generated by running:

```bash
git clone --depth 200 https://github.com/pallets/click /tmp/click
python tools/changelog/generate_changelog.py \
  --repo /tmp/click \
  --version Unreleased \
  --repo-url https://github.com/pallets/click
```

39 commits since `8.3.3` were classified into 4 Added / 18 Changed / 7 Fixed
items with linked commit hashes. Merge commits were filtered automatically.

## Tests

```bash
python tools/changelog/tests/test_changelog.py -v
# Ran 16 tests in 0.97s — OK
```

16 unittest cases covering:
- Conventional Commits prefix → bucket mapping (8 prefixes)
- Default-skipped types (`chore`, `docs`, `test`, `style`, `build`, `ci`) and `--include-skipped`
- Verb-prefix heuristics on non-conventional commits (14 subjects)
- Breaking-change detection in body (`BREAKING CHANGE:`) and subject (`feat!:`)
- Render: all 4 buckets present, breaking banner, "no notable changes" fallback, repo-url commit links
- Upsert: file creation with preamble, insertion above existing section
- End-to-end: build a real tiny repo, tag it, commit `feat:` / `fix:` / `docs:`, run the CLI and verify output + filtering + in-place file creation

## Acceptance criteria checklist

- [x] Works via `bash changelog.sh` — wrapper provided
- [x] Works as a Claude Code skill (`SKILL.md`) — drop into `.claude/skills/`
- [x] Fetches commits since the last git tag (auto-detected via `git describe --tags --abbrev=0`)
- [x] Auto-categorizes into Added / Changed / Fixed / Removed
- [x] Outputs a properly formatted `CHANGELOG.md` (Keep a Changelog 1.1.0)
- [x] Tested on a real GitHub repo (`samples/sample-pallets-click.md`)
- [x] README with setup instructions in 3 steps
