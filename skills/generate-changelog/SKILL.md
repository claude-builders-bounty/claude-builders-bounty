---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the latest Git tag.
---

# Generate Changelog

Run this skill when the user asks for `/generate-changelog` or requests a changelog from Git history.

1. Confirm the current directory is the intended Git repository.
2. Run `python3 generate_changelog.py --repo .`.
3. Review `CHANGELOG.md` for ambiguous commit subjects; never invent changes absent from Git history.
4. Report the latest tag used and the number of commits included.

The generator is deterministic, uses only local Git history, ignores merge commits, and never modifies Git history or contacts a network service.
