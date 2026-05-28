# Generate Changelog Skill

A bash script that generates a structured `CHANGELOG.md` from git history using conventional commit parsing.

## Quick Setup (3 steps)

1. **Copy the script** to your project root:
   ```bash
   cp generate-changelog.sh /path/to/your/project/
   ```

2. **Make it executable**:
   ```bash
   chmod +x generate-changelog.sh
   ```

3. **Run it**:
   ```bash
   bash generate-changelog.sh
   ```

That's it! Your `CHANGELOG.md` is ready.

## What It Does

- Parses git commits using [Conventional Commits](https://www.conventionalcommits.org/) format
- Categorizes changes into: **Added**, **Fixed**, **Changed**, **Removed**
- Links each entry to its commit
- Follows [Keep a Changelog](https://keepachangelog.com/) format

## Usage

```bash
# Default: generates CHANGELOG.md from last tag
bash generate-changelog.sh

# Custom output file
bash generate-changelog.sh docs/CHANGELOG.md

# Since specific tag
bash generate-changelog.sh CHANGELOG.md v1.0.0
```

## Sample Output

See `SAMPLE_OUTPUT.md` for an example of the generated changelog.

## Requirements

- Git repository
- Bash shell
- No external dependencies

## License

MIT
