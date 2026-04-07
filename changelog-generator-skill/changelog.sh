#!/bin/bash
# changelog.sh - Bash wrapper for CHANGELOG generator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/scripts/generate_changelog.py"

# Default values
REPO_PATH="."
SINCE_TAG=""
OUTPUT_FILE="CHANGELOG.md"
FORMAT="markdown"
INCLUDE_ALL=false

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS] [REPO_PATH]"
    echo ""
    echo "Generate structured CHANGELOG from git history"
    echo ""
    echo "Options:"
    echo "  -t, --since-tag TAG    Generate from specific tag (default: last tag)"
    echo "  -o, --output FILE      Output file (default: CHANGELOG.md)"
    echo "  -f, --format FORMAT    Output format: markdown, json, text (default: markdown)"
    echo "  -a, --all              Include all commits (not just since last tag)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Generate CHANGELOG for current repo"
    echo "  $0 /path/to/repo        # Generate for specific repository"
    echo "  $0 --since-tag v1.0.0   # Generate since v1.0.0"
    echo "  $0 --output RELEASE.md  # Output to RELEASE.md"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--since-tag)
            SINCE_TAG="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -a|--all)
            INCLUDE_ALL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            REPO_PATH="$1"
            shift
            ;;
    esac
done

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Build command
CMD="python3 \"$PYTHON_SCRIPT\" \"$REPO_PATH\""

if [[ -n "$SINCE_TAG" ]]; then
    CMD="$CMD --since-tag \"$SINCE_TAG\""
fi

CMD="$CMD --output \"$OUTPUT_FILE\""
CMD="$CMD --format \"$FORMAT\""

if [[ "$INCLUDE_ALL" == true ]]; then
    CMD="$CMD --all"
fi

# Execute command
echo "Running: $CMD"
eval "$CMD"

# Check if successful
if [[ $? -eq 0 ]]; then
    echo ""
    echo "✅ CHANGELOG generated successfully!"
    if [[ "$OUTPUT_FILE" != "-" ]]; then
        echo "📄 Output file: $OUTPUT_FILE"
        
        # Show first few lines of output
        if [[ -f "$OUTPUT_FILE" ]]; then
            echo ""
            echo "Preview:"
            head -20 "$OUTPUT_FILE"
        fi
    fi
else
    echo "❌ Failed to generate CHANGELOG"
    exit 1
fi