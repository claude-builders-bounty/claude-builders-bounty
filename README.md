# Changelog Generator

Generate a structured CHANGELOG.md from git history.

## Quick Start

### 1. Clone or download
```bash
git clone https://github.com/<your-username>/changelog-generator.git
cd changelog-generator
```

### 2. Generate a changelog
```bash
bash changelog.sh /path/to/your/repo
```

### 3. Review the output
A formatted CHANGELOG.md is created in the target repo, categorized by commit type.

## Options
```bash
bash changelog.sh [repo_path] [since_tag] [output_file]
```

| Argument      | Description                        | Default         |
|---------------|------------------------------------|-----------------|
| `repo_path`   | Path to the git repository         | Current dir     |
| `since_tag`   | Tag to start from                  | Latest tag      |
| `output_file` | Where to write the changelog       | `CHANGELOG.md`  |

## Commit Categories
- **Added** — `feat`, `feature`
- **Fixed** — `fix`, `bugfix`
- **Changed** — `refactor`, `style`, `change`
- **Performance Improvements** — `perf`
- **Removed** — `remove`, `del`, `rm`
- **Documentation** — `docs`, `doc`
- **Chores** — `chore`, `test`, `build`, `ci`
- **Other Changes** — everything else

## Claude Code Skill
This repo includes a `SKILL.md` for use with Claude Code. Run `/generate-changelog` in Claude Code to generate changelogs interactively.

## License
MIT
