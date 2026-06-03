# 📋 changelog.sh — Structured CHANGELOG Generator

Auto-generate a `CHANGELOG.md` from your project's git history using conventional commits.

## Setup (3 Steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/your-fork/main/submissions/01-changelog-skill/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Generate your changelog
./changelog.sh
```

## Requirements

- Git repository with conventional commit messages
- Bash 4+ (Linux, macOS, WSL, Git Bash)

## Commands

```bash
./changelog.sh              # Generate CHANGELOG.md
./changelog.sh HISTORY.md   # Custom output filename
```

## Integration

- **CLI**: Run from project root after each release
- **CI/CD**: Add to your release workflow
- **Claude Code**: Use `/generate-changelog` with the SKILL.md installed

## Sample Output

```
$ ./changelog.sh
✅ Changelog generated: CHANGELOG.md
   12 added | 5 fixed | 8 changed | 2 removed
```

> See [SAMPLE.md](./SAMPLE.md) for a full output example.
