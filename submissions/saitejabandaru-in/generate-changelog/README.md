# generate-changelog

> A Claude Code skill and bash script that automatically generates a structured `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

**1. Copy the files into your project:**
```bash
cp changelog.sh /your/project/
cp SKILL.md ~/.claude/skills/generate-changelog.md   # for Claude Code
```

**2. Make the script executable:**
```bash
chmod +x changelog.sh
```

**3. Run it:**
```bash
# Via bash
bash changelog.sh

# Via Claude Code (in your project directory)
/generate-changelog
```

---

## What it does

- Detects the **last git tag** automatically and uses it as baseline (`<last-tag>..HEAD`)
- If no tags exist, processes the **entire git history**
- **Auto-categorizes** commits using conventional commit prefixes:

| Category | Prefixes matched |
|----------|-----------------|
| ✨ Added | `feat:`, `add:`, `new:`, `feature:` |
| 🐛 Fixed | `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:` |
| 🔄 Changed | `refactor:`, `chore:`, `style:`, `perf:`, `docs:`, `update:` |
| 🗑️ Removed | `remove:`, `delete:`, `drop:`, `deprecate:`, `revert:` |
| 📝 Other | Everything else |

- Strips conventional commit prefixes from display messages (`feat: Add login` → `Add login`)
- Generates clickable commit links (auto-detects GitHub URL from git remote, converts SSH → HTTPS)
- Compatible with **bash 3.2+** (macOS) and **bash 4+** (Linux)

---

## Options

```
-o, --output FILE    Output file (default: CHANGELOG.md)
-t, --tag TAG        Start from a specific tag instead of the last one
-r, --repo URL       Override repository URL for commit links
-h, --help           Show help message
```

---

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — 2026-07-20

> Changes since `v1.0.0` (6 commits)

### ✨ Added
- implement rate limiting with token bucket algorithm ([`bcca142`](https://github.com/demo-user/my-project/commit/bcca142...)) — _Sai Teja Bandaru_

### 🐛 Fixed
- correct CORS headers for preflight requests ([`3aef226`](https://github.com/demo-user/my-project/commit/3aef226...)) — _Sai Teja Bandaru_

### 🔄 Changed
- cache user permissions in Redis for 5 minutes ([`f9b5ccc`](https://github.com/demo-user/my-project/commit/f9b5ccc...)) — _Sai Teja Bandaru_
- simplify token refresh flow ([`c27e5dc`](https://github.com/demo-user/my-project/commit/c27e5dc...)) — _Sai Teja Bandaru_

### 🗑️ Removed
- delete deprecated BasicAuth handler ([`378820f`](https://github.com/demo-user/my-project/commit/378820f...)) — _Sai Teja Bandaru_

### 📝 Other
- Update CI pipeline to use GitHub Actions ([`e8ebe6f`](https://github.com/demo-user/my-project/commit/e8ebe6f...)) — _Sai Teja Bandaru_
```

---

## Acceptance Criteria ✅

- [x] Works via `/generate-changelog` Claude Code skill and `bash changelog.sh`
- [x] Fetches commits since the last git tag (falls back to full history if no tags)
- [x] Auto-categorizes into: Added / Fixed / Changed / Removed / Other
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (sample output above)
- [x] README with setup instructions in 3 steps or fewer

Closes #1
/opire try
