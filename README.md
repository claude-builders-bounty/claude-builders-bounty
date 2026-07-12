# Git Changelog Generator

A lightweight Python script to automatically generate a formatted `CHANGELOG.md` file by parsing Git commit history. This tool is designed to help developers keep track of changes, features, and fixes in a clean, readable format.

## ✨ Features

- **Automated Generation:** No need to manually write down every commit.
- **Categorized Logs:** Automatically organizes commits into sections like `Features`, `Fixes`, and `Others` (based on commit messages).
- **Clean Formatting:** Produces a well-structured Markdown file ready for documentation.
- **Minimalistic & Fast:** A single-file script with no complex dependencies.

## 🚀 Getting Started

### Prerequisites

Before running the script, ensure you have the following installed:
- [Python 3.x](https://www.python.org/downloads/)
- A Git repository (the script must be run inside a Git project folder).

### Installation

1. Clone this repository or download the `changelog.py` file.
2. Place `changelog.py` in the root directory of your Git project.

### How to Use

1. Open your terminal (PowerShell, Bash, or Command Prompt).
2. Navigate to your project directory.
3. Run the script using the following command:
```bash
python changelog.py
```
### View Results
After running the script, a new file named CHANGELOG.md will be created (or updated) in your project root. You can open it with any Markdown viewer or text editor (like VS Code).

### Technical Details
The script works by executing git log commands under the hood to fetch commit messages and then uses pattern matching to categorize them.
