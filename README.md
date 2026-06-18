# 📝 Git Changelog Generator Skill

A lightweight, professional Python tool to automatically generate structured `CHANGELOG.md` files from Git history using the **Conventional Commits** specification.

## 🚀 Features

- **Automatic Categorization**: Groups commits into Features, Bug Fixes, Documentation, etc.
- **Scope Support**: Handles scoped commits (e.g., `feat(auth): add login`) and highlights them.
- **Conventional Commits**: Fully compatible with the industry-standard commit format.
- **Clean Output**: Generates a beautiful, readable Markdown file.

## 🛠 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
   cd claude-builders-bounty
   ```

2. Ensure you have Python 3.x installed.

## 📖 Usage

Run the script in the root of any Git repository:

```bash
python3 changelog_gen.py
```

The script will analyze the git log and create a `CHANGELOG.md` file in the current directory.

## 📐 Commit Format Example

To get the best results, use the following format for your commits:
- `feat(ui): add dark mode support` $\rightarrow$ **🚀 Features**
- `fix(api): resolve timeout issue` $\rightarrow$ **🐛 Bug Fixes**
- `docs(readme): update installation guide` $\rightarrow$ **📚 Documentation**
- `chore: update dependencies` $\rightarrow$ **🔧 Maintenance**

## 📄 License
MIT
