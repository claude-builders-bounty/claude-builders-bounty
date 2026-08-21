# generate-changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Usage

Run the command in any git repository:

```
/generate-changelog
```

Or use the bash script directly:

```bash
bash changelog.sh
```

## How It Works

1. Finds the last git tag to determine the commit range
2. Fetches all commits since that tag (or last 50 if no tags exist)
3. Auto-categorizes each commit by analyzing the conventional commit prefix:
   - `feat` / `add` / `create` / `implement` → **Added**
   - `fix` / `bug` / `patch` / `resolve` → **Fixed**
   - `refactor` / `change` / `update` / `modify` → **Changed**
   - `remove` / `delete` / `drop` → **Removed**
   - `doc` / `docs` / `readme` → **Documentation**
   - Everything else → **Maintenance**
4. Outputs a properly formatted `CHANGELOG.md` with commit links

## Commit Message Format

Best results with conventional commits:

```
feat(auth): add OAuth2 login flow
fix(api): resolve null pointer in user endpoint
refactor(db): migrate to connection pooling
remove(deprecated): drop legacy v1 endpoints
```

## Installation

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Run it anytime to generate/update CHANGELOG.md
cd /path/to/your/project && bash changelog.sh
```
