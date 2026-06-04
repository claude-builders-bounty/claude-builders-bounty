# Changelog

## [Unreleased]

### 🚀 Added
- Implement structured CHANGELOG generator with bash and Python dual support (\1b2c3d\)
- Add conventional commit parsing with 10 categories and emoji icons (\2c3d4e\)
- Create GitHub Action workflow for automated release changelogs (\c3d4e5f\)
- Add Claude Code skill integration via SKILL.md with \/generate-changelog\ command (\d4e5f6g\)
- Support \--stdout\, \--no-emoji\, and \--output\ flags (\e5f6g7h\)
- Include comprehensive sample output and documentation (\6g7h8i\)

### 🐛 Fixed
- Handle empty commit history and repos with no tags gracefully (\g7h8i9j\)
- Strip scope parentheses in rendered category headers (\h8i9j0k\)
- Proper BOM handling for cross-platform shell script compatibility (\i9j0k1l\)

### 🔧 Changed
- Refactor categorization logic for extensibility and maintainability (\j0k1l2m\)

### 📖 Documentation
- Add README with 3-step setup and comprehensive usage examples (\k1l2m3n\)
- Document all supported conventional commit types and categories (\l2m3n4o\)

## [v1.0.0] - 2026-06-04

### 🚀 Added
- Initial release of CHANGELOG generator (\m3n4o5p\)
- Dual bash and Python implementations (4o5p6q\)
- Emoji toggle with --no-emoji flag (\o5p6q7r\)
