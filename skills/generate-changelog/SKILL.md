name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history, auto-categorizing changes into Added, Fixed, Changed, Removed, and Other.
instructions: |
  You are a changelog generation skill. When invoked, you will run the `changelog.sh` script to produce a CHANGELOG.md file.

  Steps:
  1. Check that the current directory is a git repository
  2. Run `./changelog.sh` (or `bash changelog.sh`)
  3. If CHANGELOG.md already exists, backup it first (e.g., CHANGELOG.md.bak)
  4. Display the generated changelog to the user
  5. Offer to commit the new CHANGELOG.md

  The script categorizes commits using conventional commit prefixes. If the user wants custom categories, you may offer to edit the `changelog.sh` script.

  Output should be informative: show a summary of what was generated (number of commits, date range, breakdown by category).

trigger:
  command: "/generate-changelog"
  pattern: "generate changelog"
  description: Generate CHANGELOG.md from git history

example_interactions:
  - user: "generate changelog"
    assistant: "Running changelog generator... ✓ Generated CHANGELOG.md (154 commits since v1.0.0). Categories: Added (12), Fixed (5), Changed (8), Removed (1), Other (128)."
  - user: "/generate-changelog"
    assistant: "Creating changelog... Done. View CHANGELOG.md? (y/n)"

requirements:
  - bash
  - git

version: "1.0.0"
license: MIT
