# Changelog Generator

Generate a structured `CHANGELOG.md` from your project's git history automatically.

## Setup (3 Steps)

1. **Clone or navigate** to your repository:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Make the script executable**:
   ```bash
   chmod +x changelog.sh
   ```

3. **Run the generator**:
   ```bash
   # Using bash script
   ./changelog.sh

   # Or specify a custom output path
   ./changelog.sh docs/CHANGELOG.md

   # Or use Claude Code skill
   # Run: /generate-changelog
   ```

That's it — a `CHANGELOG.md` will be created in your repository root, auto-categorized by conventional commit type.

## Conventional Commit Types Supported

| Prefix     | Category  |
|------------|-----------|
| `feat`     | Added     |
| `fix`      | Fixed     |
| `refactor` | Changed   |
| `docs`     | Changed   |
| `chore`    | Changed   |
| `style`    | Changed   |
| `perf`     | Changed   |
| `build`    | Changed   |
| `ci`       | Changed   |
| `test`     | Changed   |
| `revert`   | Removed   |

## Sample Output

See [`CHANGELOG.md`](./CHANGELOG.md) for an example generated from this project.
