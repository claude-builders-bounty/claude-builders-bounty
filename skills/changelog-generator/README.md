# changelog-generator

Generate a [Keep-A-Changelog](https://keepachangelog.com/en/1.1.0/)–formatted `CHANGELOG.md` from a project's git history. Auto-categorizes commits into **Added / Changed / Fixed / Removed** using conventional-commit prefixes with keyword fallback.

## Setup (3 steps)

1. Drop this `changelog-generator/` directory anywhere a Claude Code session can read it (or `git submodule add` it). Both `scripts/changelog.py` and `scripts/changelog.sh` are zero-dependency.
2. From your project root, run **either** of:
   - `python path/to/scripts/changelog.py --out CHANGELOG.md`
   - `bash path/to/scripts/changelog.sh --out CHANGELOG.md`
3. Or, inside Claude Code, just say `/generate-changelog` — the [SKILL.md](SKILL.md) wires it up automatically.

That's it. The script picks up the latest annotated tag (or the project's first commit if there are no tags) and walks forward to `HEAD`.

## Options

| Flag         | Default            | Meaning                                                  |
|--------------|--------------------|----------------------------------------------------------|
| `--since`    | latest tag         | Override the start ref (any tag/SHA)                     |
| `--until`    | `HEAD`             | Override the end ref                                     |
| `--out`      | stdout             | Write to a file. Prepends to existing `CHANGELOG.md`.    |
| `--version`  | `Unreleased`       | Override the label in the new section heading           |

## Sample output

See [samples/CHANGELOG.example.md](samples/CHANGELOG.example.md) — generated from the very repo this skill lives in.

## How categorization works

| Bucket   | Conventional-commit prefixes                                            | Keyword fallback (case-insensitive)               |
|----------|--------------------------------------------------------------------------|---------------------------------------------------|
| Added    | `feat`, `add`                                                            | add, introduce, new                                |
| Changed  | `refactor`, `perf`, `style`, `chore`, `docs`, `build`, `ci`, `test`, `deps` | update, change, improve, bump, rename             |
| Fixed    | `fix`, `bugfix`, `patch`                                                 | fix, repair, correct, resolve                      |
| Removed  | `revert`, `remove`                                                       | remove, drop, delete                               |
| Other    | (everything else — never silently dropped)                               | —                                                  |

## License

MIT (matches the parent repo).
