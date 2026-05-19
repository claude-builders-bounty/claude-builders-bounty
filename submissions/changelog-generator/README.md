# CHANGELOG Generator for Claude Code

A Claude Code skill / standalone script that generates a structured `CHANGELOG.md` from git history.

## Setup (2 steps)

```bash
# 1. Make the script executable
chmod +x changelog.sh

# 2. Run it in any git repository
bash changelog.sh
```

That's it. A `CHANGELOG.md` will be generated in the current directory.

## As a Claude Code Skill

Copy `SKILL.md` and `changelog.sh` into your project's skill directory, then use:

```
/generate-changelog
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--repo` | Path to git repository | `.` (current dir) |
| `--from-tag` | Start from this tag | Latest tag |
| `--output` | Output file path | `CHANGELOG.md` |
| `--repo-url` | Base URL for commit links | None |

## Sample Output

Generated from a real repo (OpenClaw workspace):

```
✅ Generated CHANGELOG.md from v1.0.0..HEAD
   42 commits categorized
```

## How it works

1. Detects the latest git tag
2. Fetches all commits between that tag and HEAD  
3. Categorizes by conventional commit prefix / keywords
4. Outputs structured Markdown with Added/Fixed/Changed/Removed sections

## License

MIT
