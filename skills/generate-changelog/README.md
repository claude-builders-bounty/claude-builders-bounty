# generate-changelog

Generate a structured `CHANGELOG.md` from your git history.

## Setup (3 steps)

```bash
git clone https://github.com/anlogrian-rgb/generate-changelog.git
cd generate-changelog
./changelog.sh /path/to/your/repo
```

That's it. It writes `CHANGELOG.md` in the target repo.

## Example output

```markdown
# Changelog

## [Unreleased]

### Added
- new auth system (abc1234)

### Fixed
- empty git history (87addf7)

### Changed
- simplify category parsing (b1ed7aa)

### Removed
- deprecated flag (3324e34)
```

## How it categorises

| Commit prefix | Category |
|---|---|
| feat, feature, add, new | Added |
| fix, bugfix, hotfix | Fixed |
| refactor, style, change, update, perf | Changed |
| remove, delete, rm, deprecat | Removed |

## License

MIT
