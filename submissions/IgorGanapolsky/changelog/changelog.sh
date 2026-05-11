#!/bin/bash
# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install it."
    exit
fi

# Run the generator
python3 "$(dirname "$0")/generate_changelog.py"
