# Git Changelog Generator Skill for Claude Code 📝

Automatically generate structured, [Keep a Changelog](https://keepachangelog.com/) compliant `CHANGELOG.md` files from your git commit history.

Bounty #1 submission for **Claude Builders Bounty** ($50 — powered by Opire).

---

## ⚡ Setup & Usage in 3 Steps

### Step 1: Install
Copy the skill and script into your repository or Claude skills folder:
```bash
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/changelog-generator/changelog.sh -o /usr/local/bin/generate-changelog && chmod +x /usr/local/bin/generate-changelog
```

### Step 2: Run
In your project root (any git repo), run:
```bash
generate-changelog
```
*(Or inside Claude Code, run `/generate-changelog`)*

### Step 3: View Result
Open `CHANGELOG.md` — your commits are automatically categorized into `Added`, `Fixed`, `Changed`, `Removed`, and `Security` with commit hashes.

---

## 📋 Features & Acceptance Criteria Checklist
- [x] **Triggers**: Invoked via Claude Code `/generate-changelog` command or `bash changelog.sh`.
- [x] **Tag Tracking**: Identifies the latest git tag and parses commits up to `HEAD`.
- [x] **Auto-Categorization**: Sorts into `Added`, `Fixed`, `Changed`, `Removed`, and `Security`.
- [x] **Standard Output**: Generates valid Markdown formatted per Keep a Changelog v1.0.0.
- [x] **Sample Included**: Real-world output included in `examples/CHANGELOG.md`.
- [x] **Setup in <= 3 steps**: Quickstart documented above in 3 steps.
