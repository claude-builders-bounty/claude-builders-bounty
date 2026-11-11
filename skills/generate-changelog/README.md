# Generate Changelog Skill

> Automatically generate structured `CHANGELOG.md` files from git history adhering to [Keep a Changelog](https://keepachangelog.com/).

---

## ⚡ Setup & Usage in 3 Steps

### Step 1: Add to your repository
Copy `skills/generate-changelog` into your project:
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/cbb
cp -r /tmp/cbb/skills/generate-changelog ./skills/
```

### Step 2: Run the script
Run the generator from your repository root:
```bash
bash skills/generate-changelog/changelog.sh
```

### Step 3: Review your CHANGELOG.md
Inspect the generated or updated `CHANGELOG.md` file:
```bash
git diff CHANGELOG.md
```

---

## 🛠️ CLI Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| `-o, --output <file>` | Path to output markdown file | `CHANGELOG.md` |
| `-t, --tag <version>` | Target release version header | `Unreleased` |
| `-s, --since <tag>` | Start commit range from specific tag | Latest git tag |
| `-d, --dry-run` | Print markdown to terminal without modifying files | `false` |
| `-h, --help` | Display usage instructions | - |

---

## 🤖 Claude Code Integration

When installed in `.claude/skills/generate-changelog` or `skills/generate-changelog`, Claude Code recognizes the `/generate-changelog` slash command to automatically parse recent commits and document project releases.
