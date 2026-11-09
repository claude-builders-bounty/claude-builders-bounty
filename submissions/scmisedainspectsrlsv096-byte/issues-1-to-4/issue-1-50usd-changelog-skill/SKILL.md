---
name: changelog-generator
description: Generates a structured Keep-a-Changelog / Semantic Versioning CHANGELOG.md from git commit history and tags.
---

# Structured CHANGELOG Generator Skill

## Instructions

1. **Inspect Git Tags & Commit Range:**
   Determine the latest tag (or initial commit if no tags exist):
   ```bash
   LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
   git log "${LAST_TAG}..HEAD" --pretty=format:"%h|%s|%an|%ad" --date=short
   ```
2. **Categorize Commits by Conventional Commit Prefix:**
   - **🚀 Added (`feat`)**: New user-facing features or capabilities
   - **🐛 Fixed (`fix`)**: Bug fixes and regression patches
   - **⚡ Performance (`perf`)**: Speed, memory, or query optimizations
   - **🔒 Security (`sec` / security fixes)**: Vulnerability patches and hardening
   - **🔧 Changed / Refactored (`refactor`, `build`, `chore`, `docs`)**: Significant internal or documentation updates (omit trivial typo/merge commits)
   - **⚠️ Breaking Changes (`BREAKING CHANGE` or `!:`):** Highlight at the top of the release section with migration notes.
3. **Output Format:**
   Prepend the new release block under `## [Unreleased]` (or `## [vX.Y.Z] - YYYY-MM-DD`) in `CHANGELOG.md`, linking each entry to its short commit SHA and PR number if present.
