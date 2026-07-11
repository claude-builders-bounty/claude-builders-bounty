# CHANGELOG Generator

This script automatically generates a structured CHANGELOG.md from git history.

## Setup

1. Save the `changelog.sh` script in your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run the script: `./changelog.sh`

## Usage

The script will generate a CHANGELOG.md file with changes categorized as Added, Fixed, Changed, or Removed based on your commit history since the last git tag.