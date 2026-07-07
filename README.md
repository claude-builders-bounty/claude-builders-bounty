# Changelog Generator

This Python script (`generate_changelog.py`) automatically generates a structured `CHANGELOG.md` from a project's git history.

## Setup

1.  Clone this repository:
    ```bash
    git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
    cd claude-builders-bounty
    ```
2.  Ensure Python 3 is installed and accessible.

## Usage

Run the script from the root of your git repository:

```bash
python3 generate_changelog.py
```

This will generate a `CHANGELOG.md` file in the current directory, categorizing commits into `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Sample Output

See the generated `CHANGELOG.md` for a sample.