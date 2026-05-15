# CHANGELOG Generator — Setup

## 3-Step Setup

```bash
# 1. Copy the script into your repo
cp changelog.py changelog-skill/ /your/project/
cd /your/project

# 2. Make executable (Unix)
chmod +x changelog-skill/changelog.py

# 3. Generate!
python changelog-skill/changelog.py
```

That's it. `CHANGELOG.md` is created (or updated with new version prepended).

## Requirements

- **Python 3.8+** (no dependencies)
- **Git** (any version)

## Verify

```bash
python changelog-skill/changelog.py --stdout
```

See `SAMPLE_OUTPUT.md` for example output.