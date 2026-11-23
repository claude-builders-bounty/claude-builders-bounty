# Changelog Generator Skill 📝

Generate a clean, structured `CHANGELOG.md` directly from git history following the [Keep a Changelog](https://keepachangelog.com/) standard.

Categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed**.

---

## 3-Step Setup

1. **Copy the script to your project**:
   ```bash
   cp changelog.sh /path/to/your/project/
   ```

2. **Run the generator**:
   ```bash
   bash changelog.sh
   ```

3. **Verify the generated `CHANGELOG.md`**:
   ```bash
   cat CHANGELOG.md
   ```

*(Alternatively, if using Claude Code, trigger with `/generate-changelog`)*

---

## Command Options

| Command | Action |
|---------|--------|
| `bash changelog.sh` | Generates or replaces `CHANGELOG.md` with commits since last tag |
| `bash changelog.sh --stdout` | Prints changelog to stdout without writing a file |
| `bash changelog.sh --prepend` | Prepends new release section to existing `CHANGELOG.md` |
| `bash changelog.sh --version-title "v1.2.0"` | Specifies the release version title |
| `bash changelog.sh --since-tag "v1.0.0"` | Fetches commits since a specific tag |
| `bash changelog.sh --all` | Generates changelog across all commits |

---

## Run Verification Tests

```bash
python3 skills/generate-changelog/test_changelog.py
```
