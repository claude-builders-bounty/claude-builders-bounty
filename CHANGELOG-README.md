# changelog.sh

A production-quality bash script that generates a structured `CHANGELOG.md` from your git history using [Conventional Commits](https://www.conventionalcommits.org/).

## Quick Setup (3 Steps)

### 1. Clone or copy the script

```bash
cp changelog.sh /path/to/your/repo/changelog.sh
chmod +x /path/to/your/repo/changelog.sh
```

### 2. Tag your releases

```bash
git tag v1.0.0   # mark a release point
```

### 3. Generate the changelog

```bash
bash changelog.sh
```

That's it. A `CHANGELOG.md` will be created in your repo root.

## How It Works

The script reads commits since the last git tag and categorizes them by their [Conventional Commit](https://www.conventionalcommits.org/) prefix:

| Prefix       | Category  |
|--------------|-----------|
| `feat:`      | Added     |
| `fix:`       | Fixed     |
| `refactor:`  | Changed   |
| `remove:`    | Removed   |
| `delete:`    | Removed   |
| `perf:`, `style:`, `docs:`, `test:`, `ci:`, `build:`, `chore:` | Changed |

Unrecognized prefixes default to **Changed**.

## Options

```
bash changelog.sh [OPTIONS]

  -o, --output FILE    Output file (default: CHANGELOG.md)
  -t, --tag TAG        Tag to start from (default: latest tag)
  -r, --repo PATH      Git repository path (default: .)
  -d, --date DATE      Release date (default: today)
  -f, --format FORMAT  Output format: markdown|json (default: markdown)
  -h, --help           Show help
```

## Examples

```bash
# Generate changelog since the latest tag
bash changelog.sh

# Generate for a specific tag with custom output
bash changelog.sh --tag v1.2.0 --output docs/CHANGELOG.md

# Generate JSON output for CI pipelines
bash changelog.sh --format json --output changelog.json

# Point to a different repo
bash changelog.sh --repo /path/to/other/project
```

## Sample Output

```markdown
# Changelog

## [v1.2.0] — 2026-06-23

### Added
- feat: add user authentication (`a1b2c3d`)
- feat(api): rate limiting endpoint (`e4f5g6h`)

### Fixed
- fix: resolve null pointer on login (`i7j8k9l`)

### Changed
- refactor: extract database module (`m0n1o2p`)
```

## CI Integration

Add to your GitHub Actions workflow:

```yaml
- name: Generate changelog
  run: bash changelog.sh --format json --output changelog.json

- name: Create release
  uses: actions/create-release@v1
  with:
    body_path: CHANGELOG.md
```

## Requirements

- Git (any modern version)
- Bash 4+ (standard on Linux/macOS with Homebrew)

## License

MIT
