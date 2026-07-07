# Git Changelog Generator Skill

Automatically generates a structured `CHANGELOG.md` file from your git history.

## `/generate-changelog` command

When the user asks to generate a changelog or types `/generate-changelog`, execute the following workflow:

1. Check if git is initialized in the workspace.
2. Locate the `changelog.sh` script or download it.
3. Run the script: `bash changelog.sh`.
4. Present the generated `CHANGELOG.md` to the user.

## Setup Instructions

1. Copy the `changelog.sh` script into the root of your repository.
2. Run `chmod +x changelog.sh` to make it executable.
3. Execute it using `bash changelog.sh` or `./changelog.sh`.
