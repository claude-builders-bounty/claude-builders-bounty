# CLAUDE.md Template Generator

Generate a comprehensive CLAUDE.md file for Next.js + SQLite projects.

## Quick Setup (2 Steps)

1. **Copy** `claude-template/` to your project
2. **Run** `python claude-template/claude_generator.py "My Project"`

## Features

- 🎯 Complete Next.js + SQLite project template
- 📚 Comprehensive CLAUDE.md with development guidelines
- 🔧 Auto-generates package.json, tsconfig.json, tailwind.config.ts
- 🗄️ Database utilities and connection patterns
- 🔒 Security best practices
- 🧪 Testing setup

## Usage

```bash
# Generate in current directory
python claude_generator.py "My Awesome Project"

# Generate in specific directory
python claude_generator.py "My Project" -o ./my-project

# Preview without writing
python claude_generator.py "My Project" --dry-run

# Custom colors
python claude_generator.py "My Project" \
  --primary-color="#ff0000" \
  --secondary-color="#00ff00"
```

## Generated Files

| File | Description |
|------|-------------|
| `CLAUDE.md` | Complete project documentation |
| `package.json` | Dependencies and scripts |
| `tsconfig.json` | TypeScript configuration |
| `next.config.js` | Next.js configuration |
| `tailwind.config.ts` | Tailwind CSS configuration |
| `lib/db.ts` | Database utilities |

## CLAUDE.md Contents

- Project overview and tech stack
- Directory structure
- Quick start guide
- Database architecture
- API route patterns
- Component patterns
- Security best practices
- Common issues and solutions

## Bounty

Part of [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) #2 ($75)
