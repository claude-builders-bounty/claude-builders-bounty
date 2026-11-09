# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Project Overview

{{PROJECT_NAME}}
{{PROJECT_DESCRIPTION}}

## Tech Stack

- **Language:** {{LANGUAGE}}
- **Framework:** {{FRAMEWORK}}
- **Package Manager:** {{PACKAGE_MANAGER}} (npm / yarn / pnpm)
- **Test Runner:** {{TEST_RUNNER}} (Jest / Vitest / Mocha)
- **Linter:** {{LINTER}} (ESLint / Prettier)

## Project Structure

```
├── src/                 # Source code
├── tests/               # Test files
├── dist/                # Build output (gitignored)
├── node_modules/        # Dependencies (gitignored)
├── package.json         # Dependencies & scripts
├── tsconfig.json        # TypeScript config (if applicable)
├── .eslintrc            # ESLint config (if applicable)
├── .prettierrc          # Prettier config (if applicable)
└── README.md            # Project README
```

## Available Scripts

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run linting
npm run lint

# Run type check (TypeScript)
npx tsc --noEmit
```

## Code Conventions

### General
- Use 2 spaces for indentation
- Use single quotes for strings
- Add trailing commas in multiline objects/arrays
- Name files in kebab-case (e.g., `user-service.js`)
- Name components in PascalCase (e.g., `UserProfile.jsx`)

### TypeScript (if applicable)
- Avoid `any` — use explicit types or `unknown`
- Export interfaces for public API shapes
- Enable `strict` mode in tsconfig.json

### Testing
- Write tests for all new functions
- Test file naming: `*.test.js` or `*.test.ts`
- Aim for 80%+ code coverage

## Common Tasks

### Add a new feature
1. Create source file in `src/`
2. Create corresponding test in `tests/`
3. Run `npm test` to verify
4. Run `npm run lint` to check style

### Fix a bug
1. Reproduce the issue
2. Write a failing test
3. Fix the code
4. Run `npm test` to confirm fix

## AI Agent Guidelines

1. **Always run tests** after making changes: `npm test`
2. **Always run lint** before submitting: `npm run lint`
3. **Run type check** for TypeScript: `npx tsc --noEmit`
4. **Keep changes small** — one PR per feature/fix
5. **Update README** if you change setup or usage
