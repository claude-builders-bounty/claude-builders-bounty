# Changelog Generator

This project provides a simple bash script to automatically generate a structured `CHANGELOG.md` from your Git history. It fetches commits since the last Git tag and categorizes them into "Added", "Fixed", "Changed", and "Removed" sections.

## Features

*   **Automatic Commit Range**: Fetches commits from the last Git tag to `HEAD`. If no tags exist, it uses the entire history.
*   **Smart Categorization**: Uses keywords and conventional commit prefixes (e.g., `feat:`, `fix:`) to categorize commits.
*   **Markdown Output**: Generates a clean, properly formatted `CHANGELOG.md`.
*   **GitHub Integration**: Automatically detects your GitHub repository URL to create direct links to commits.
*   **Incremental Updates**: Prepends new changelog entries to an existing `CHANGELOG.md` file.

## Setup Instructions

1.  **Save the script**:
    Save the `changelog.sh` script into your project's root directory.

2.  **Make it executable**:
    Open your terminal, navigate to your project's root, and run:
    