# Git Changelog Generator

A simple bash script to automatically generate a structured `CHANGELOG.md` from your git history since the last tag.

## 🚀 Features
- **Automatic Range Detection**: Finds the latest git tag and fetches all commits since then.
- **Smart Categorization**: Automatically sorts commits into `Added`, `Fixed`, `Changed`, and `Removed` based on common keywords.
- **Clean Output**: Generates a professionally formatted Markdown file.

## 🛠 Installation

1. Copy the `changelog.sh` script to your project root.
2. Make it executable:
   \`\`\`bash
   chmod +x changelog.sh
   \`\`\`

## 📖 Usage

Run the script from the root of your git repository:
\`\`\`bash
./changelog.sh
\`\`\`

The script will create or overwrite a `CHANGELOG.md` file in the current directory.

## ⚙️ Categorization Logic
The script uses the following keywords to categorize commits:
- **Added**: `Added`, `feat`, `new`
- **Fixed**: `Fixed`, `fix`, `bug`
- **Changed**: `Changed`, `update`, `refactor` (and any others not matching above)
- **Removed**: `Removed`, `deprecate`

## 📝 Example Output
\`\`\`markdown
# Changelog

## Latest Changes

### 🚀 Added
- feat: add user authentication system
- Added support for dark mode

### 🐛 Fixed
- fix: resolve memory leak in data processor
- bug: fix crash on empty input
\`\`\`
