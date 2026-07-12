---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from a project's git history since the last tag.
---

# generate-changelog

## Instructions

When the user asks you to generate a changelog or types `/generate-changelog`:

1.  **Fetch Commits**: Run a terminal command to fetch all commit messages since the last git tag. If there is no git tag, fetch all commit messages.
    *   Command to get last tag: `git describe --tags --abbrev=0`
    *   Command to get commits since tag: `git log <LAST_TAG>..HEAD --pretty=format:"%h - %s"`
    *   Command if no tags exist: `git log --pretty=format:"%h - %s"`

2.  **Analyze and Categorize**: Read the fetched commit messages and intelligently categorize them into the following sections based on their meaning:
    *   `Added`: New features, capabilities, or files.
    *   `Fixed`: Bug fixes, error resolutions, or patches.
    *   `Removed`: Deleted features, files, or deprecations.
    *   `Changed`: Refactors, updates, chore tasks, formatting, or anything that doesn't fit the above.

3.  **Generate Output**: Create or overwrite `CHANGELOG.md` in the project root with the categorized list. Use the following Markdown structure:

    ```markdown
    # Changelog

    ## [Unreleased / Latest]

    ### Added
    - [commit-hash] - Description of added feature

    ### Fixed
    - [commit-hash] - Description of bug fix

    ### Changed
    - [commit-hash] - Description of change

    ### Removed
    - [commit-hash] - Description of removed feature
    ```

    *Only include sections that have at least one commit.*

4.  **Confirm**: Notify the user that `CHANGELOG.md` has been successfully generated and formatted.
