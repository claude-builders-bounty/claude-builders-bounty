---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from a project's git history since the last release tag. It dynamically categorizes commits.
---
# Description
Automatically generates a fully structural `CHANGELOG.md` entry utilizing the local git history, formatting it neatly according to 'Keep a Changelog' guidelines.

# Instructions
1. Discover the last Git Tag: Read the most recent git tag utilizing `git describe --tags --abbrev=0`.
2. Extract Commit History: Extract a raw list of the latest commit messages running `git log <LAST_TAG>..HEAD --pretty=format:"%s"`. If there are no tags, extract the entire git history string.
3. Analyze and Categorize: Evaluate the raw log string. Logically categorize all the commit messages into Markdown sections: "Added", "Fixed", "Changed", "Removed". Discard irrelevant, aesthetic, or redundant commits.
4. Auto-Formatting: Provide a structured Markdown output under a `## [Unreleased] - YYYY-MM-DD` header (use today's date).
5. User Prompting: Present the generated markdown payload to the user for final review.
6. Execution: After the user approves, directly prepend this generated structure into the existing `CHANGELOG.md` file (or create it if it doesn't exist). Ensure you maintain prior entries unmodified.
7. Completion: Print "CHANGELOG updated successfully!"
