# Changelog Generator

Auto-generate structured CHANGELOG.md from git history.

## Setup (3 steps)

1. **Download** the script:
   ```bash
   wget https://raw.githubusercontent.com/nms131339-jpg/claude-builders-bounty/main/solutions/changelog-skill/changelog.sh
   chmod +x changelog.sh
   ```

2. **Run it** in any git repo:
   ```bash
   ./changelog.sh
   ```

3. **Done!** `CHANGELOG.md` is generated with commits categorized into Added / Fixed / Changed / Removed.

## Options

```bash
./changelog.sh v1.0.0    # Start from a specific tag
./changelog.sh            # Auto-detect latest tag (default)
```

## Sample Output

See `SAMPLE_OUTPUT.md` for a real-world example.
