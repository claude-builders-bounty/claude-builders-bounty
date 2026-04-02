#!/bin/bash
# changelog.sh - Bash wrapper for changelog generator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/changelog_generator.py"

# Default values
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
ALL_COMMITS=false
REPO_PATH="."
FORMAT="markdown"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --since|-s)
            SINCE_TAG="$2"
            shift 2
            ;;
        --all|-a)
            ALL_COMMITS=true
            shift
            ;;
        --repo|-r)
            REPO_PATH="$2"
            shift 2
            ;;
        --format|-f)
            FORMAT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -o, --output FILE    Output file (default: CHANGELOG.md)"
            echo "  -s, --since TAG      Start from specific tag"
            echo "  -a, --all            Include all commits (ignore tags)"
            echo "  -r, --repo PATH      Repository path (default: current directory)"
            echo "  -f, --format FORMAT  Output format: markdown, json (default: markdown)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed or not in PATH"
    exit 1
fi

# Build command arguments
CMD_ARGS=()
[[ -n "$OUTPUT_FILE" ]] && CMD_ARGS+=("--output" "$OUTPUT_FILE")
[[ -n "$SINCE_TAG" ]] && CMD_ARGS+=("--since" "$SINCE_TAG")
[[ "$ALL_COMMITS" == true ]] && CMD_ARGS+=("--all")
[[ -n "$REPO_PATH" ]] && CMD_ARGS+=("--repo" "$REPO_PATH")
[[ -n "$FORMAT" ]] && CMD_ARGS+=("--format" "$FORMAT")

# Run the Python script
echo "Generating changelog..."
python3 "$PYTHON_SCRIPT" "${CMD_ARGS[@]}"

echo "Done!"