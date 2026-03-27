# Technical Specification: Git Changelog Generator

## 🎯 Core Engine
- **Source**: Local Git Repository (`.git/`).
- **Input**: Command Line Arguments (Path, Since, Format).
- **Parser**: Conventional Commits (Regex-based).

## 🔌 Git CLI Integration
- **Root Detection**: `git rev-parse --show-toplevel`.
- **Log Extraction**: `git log --pretty=format:"%H%x09%ad%x09%s" --date=iso`.
- **Tag Discovery**: `git tag -l --sort=-creatordate`.

## 🛡 Parsing Rules (Conventional Commits)
- **Regex**: `^(\w+)(?:\(([^)]+)\))?!?: (.+)$`
- **Mapping**:
    - `feat` -> Features
    - `fix` -> Bug Fixes
    - `docs` -> Documentation
    - `refactor` -> Code Refactoring
    - `perf` -> Performance Improvements
    - `test` -> Testing
    - `chore` -> Maintenance

## 📊 Output Schema (Markdown)
```markdown
# Changelog

## [Version] - YYYY-MM-DD
### 🚀 Features
- [desc] ([sha])

### 🐛 Bug Fixes
- [desc] ([sha])
```
