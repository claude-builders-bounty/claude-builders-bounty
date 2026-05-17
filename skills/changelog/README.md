# CHANGELOG Generator

A Claude Code skill that auto-generates a structured `CHANGELOG.md` from git history.

## 3-Step Setup

1. **Copy the skill** to your project:
   ```bash
   cp -r skills/changelog /path/to/your/project/skills/
   ```

2. **Run it** in your git repository:
   ```bash
   python skills/changelog/changelog.py
   ```

3. **Check the output** — `CHANGELOG.md` appears in your project root.

## Options

```bash
python skills/changelog/changelog.py --output my_changelog.md --repo /path/to/repo
```

## Requirements

- Python 3.6+
- Git (installed and in PATH)

## Sample Output

See `SAMPLE_CHANGELOG.md` in this directory.
