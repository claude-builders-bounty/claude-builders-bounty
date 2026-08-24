\# Generate Changelog Skill



Automatically generates a structured `CHANGELOG.md` file from git history since the latest git tag.



\## Usage

Run `/generate-changelog` or execute `bash changelog.sh`.



\## Implementation Instructions for Claude Code

1\. Determine the latest git tag using `git describe --tags --abbrev=0`. If no tags exist, fetch all commit history from the initial commit.

2\. Retrieve commit messages between the latest tag and `HEAD` using `git log <last-tag>..HEAD --oneline` (or `git log --oneline` if no tags exist).

3\. Parse and categorize commits into standard Keep a Changelog sections:

&#x20;  - \*\*Added\*\*: New features (`feat:`, `add:`, `new:`)

&#x20;  - \*\*Fixed\*\*: Bug fixes (`fix:`, `bug:`)

&#x20;  - \*\*Changed\*\*: Refactors, updates, chore (`change:`, `refactor:`, `chore:`, `style:`)

&#x20;  - \*\*Removed\*\*: Deprecated or deleted functionality (`remove:`, `deprecate:`)

4\. Format output strictly adhering to standard Keep a Changelog conventions.

5\. Write or prepend the result into `CHANGELOG.md`.

