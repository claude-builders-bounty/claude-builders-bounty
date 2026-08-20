---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from project git history following Keep a Changelog standards.
version: 1.0.0
---

# Generate Changelog Skill

Run `/generate-changelog` or `bash changelog.sh` to extract git commits, categorize them (Conventional Commits), and write a clean `CHANGELOG.md`.

## Instructions
1. Inspect git log for recent tags or commits.
2. Group commits into Added (feat), Fixed (fix), Performance (perf), Docs (docs), and Maintenance.
3. Write or append to `CHANGELOG.md`.
