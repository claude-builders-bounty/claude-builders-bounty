#!/bin/bash

# Simple test script for changelog.sh
mkdir test_repo
cd test_repo
git init
git commit --allow-empty -m "Initial commit"
git commit --allow-empty -m "feat: initial feature"
git commit --allow-empty -m "fix: initial bug"
git commit --allow-empty -m "update: something changed"
git commit --allow-empty -m "remove: deleted old file"

cp ../changelog.sh .
bash changelog.sh

if [ -f "CHANGELOG.md" ]; then
    cat CHANGELOG.md
    echo "Test passed."
else
    echo "Test failed."
    exit 1
fi
cd ..
rm -rf test_repo
