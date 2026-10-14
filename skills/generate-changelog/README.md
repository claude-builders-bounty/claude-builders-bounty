# generate-changelog

A Claude Code **skill** plus a standalone **bash script** that turns your git history
into a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) section. Every line comes
from `git log` — nothing is invented.

## Setup (3 steps)

```bash
# 1. copy the skill into your project
mkdir -p .claude/skills && cp -r generate-changelog .claude/skills/

# 2. make the script executable
chmod +x .claude/skills/generate-changelog/changelog.sh

# 3. use it (Claude Code: /generate-changelog) or standalone:
bash .claude/skills/generate-changelog/changelog.sh --stdout
```

Writing the file instead of printing it is one more command: `bash .claude/skills/generate-changelog/changelog.sh 1.2.0`
inserts a `## [1.2.0]` section **above** the previous ones in `CHANGELOG.md`.

## Sample output (real repository)

Generated from [`tj/commander.js`](https://github.com/tj/commander.js) at `HEAD`
(1,517 commits, last tag `v15.0.0`), for the range since `v14.0.2`:

```bash
git clone https://github.com/tj/commander.js && cd commander.js
bash changelog.sh --stdout --since v14.0.2
```

```markdown
## [Unreleased] - 2026-10-14

<sub>Changes since `v14.0.2`.</sub>

### Added
- Modernise tsconfig targets, and add .cjs (#2481)
- Add describe wrappers so test output makes sense without filenames (#2472)

### Fixed
- Fix release dates in changelog (#2523)
- **examples:** Use dash separator to avoid MINGW64 path expansion (#2475)
- Fix support backing details (#2448)

### Changed
- Pin GitHub actions with hash (#2521)
- Update details for 15.0.0 release (#2519)
- Use node:util stripVTControlCharacters instead of own code (#2486)
- Switch from Jest to Node.js built-in test runner (#2463)
- List excess arguments in error message (#2384)

### Removed
- Drop EOL node 20 from test matrix, and add node 26  (#2520)
- Remove jest esm examples (#2517)
```

The `Changed` block is trimmed here; the real output contains 22 entries. Dependency
bumps and release commits (`Bump eslint from …`, `14.0.3`) are skipped by default — see
`--all` below.

## How commits are grouped

| Commit prefix | Section |
| --- | --- |
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `perf:`, `style:`, `change:`, `update:`, `improve:`, `tweak:` | Changed |
| `remove:`, `delete:`, `drop:`, `revert:`, `deprecate:` | Removed |
| `docs:`, `doc:`, `chore:`, `test:`, `ci:`, `build:`, `release:`, `bump:`, `deps:` | skipped unless `--all` |
| anything else | keyword heuristics (`add …` → Added, `fix/bug` → Fixed, `remove/delete` → Removed), else Changed |

- `feat(api): add pagination` → `- **api:** Add pagination` (scope kept, prefix dropped).
- `feat!:` or a body containing `BREAKING CHANGE:` → repeated in a `### Breaking changes`
  block at the top of the section.
- Merge commits and bare version subjects (`1.2.3`, `v1.2.3`) never generate entries.

## Options

| Flag | Effect |
| --- | --- |
| `[VERSION]` | Section title, e.g. `1.2.0`; defaults to `[Unreleased]` |
| `--stdout` | Print the section, write nothing |
| `--file <path>` | Output file (default `CHANGELOG.md`) |
| `--since <ref>` | Start after this ref (default: the last tag, else the whole history) |
| `--all` | Include maintenance commits (docs, chore, deps bumps, version bumps) |
| `--hashes` | Append the short hash to every entry |
| `-h`, `--help` | Usage |

## Tests

```bash
bash test/run-tests.sh     # builds throwaway repos, needs git and bash
```

`RESULTADO: 30 pasaron, 0 fallaron` — 30 checks covering the four sections, scope
formatting, breaking changes, the no-tag fallback, the empty range, dependency-bump
filtering, one-entry-per-line formatting, `--all`, `--hashes`, file creation and the
newest-first insertion order.

Two real bugs were found and fixed by these tests while writing the skill:

1. `git log --pretty=format:` does not terminate the last line with a newline, and
   `while read` drops a final unterminated line — so the **oldest commit of every range
   was silently missing**. Fixed by using `tformat:`, which terminates each entry.
2. Command substitution strips trailing newlines, so two entries could end up **glued on
   the same line**. Fixed by appending an explicit separator and stripping only the last
   one. Both cases are now assertions in the suite.

## Notes and limits

- Requires only `bash` and `git`; no other dependency.
- Only commits reachable from `HEAD` are considered, and empty ranges say so instead of
  printing an empty list.
- The categorisation is textual by design: a project that writes plain prose commits
  (`Fix the parser`) still lands in the right section through the keyword heuristics, but
  a subject that merely *contains* "fix" is treated as a fix.
- Existing files are edited in place (newest section on top) and a `.bak` is not created —
  use `--stdout` if you want to review before writing.

MIT, like the rest of this repository.
