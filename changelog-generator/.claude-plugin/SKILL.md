---
name: Generate Changelog
description: Semantically categorizes git commits into a structured CHANGELOG.md file.
---

This skill triggers when the user asks to generate a changelog. It instructs the assistant to use the `generate-changelog` command to find the last git tag, fetch all subsequent commits, semantically categorize them into `Added`, `Fixed`, `Changed`, or `Removed`, and output the result to `CHANGELOG.md`.

