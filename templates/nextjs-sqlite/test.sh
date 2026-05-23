#!/bin/bash

# Test script for Next.js SQLite CLAUDE.md template
echo "Testing Next.js SQLite template..."

mkdir test-next-sqlite
cd test-next-sqlite

# Mock typical project files
mkdir -p app components/ui db lib actions
touch package.json
touch db/schema.ts
touch db/queries.ts

# Copy CLAUDE.md
cp ../CLAUDE.md .

# Verify CLAUDE.md exists and has content
if [ -s "CLAUDE.md" ] && grep -q "Next.js 15 App Router + SQLite" CLAUDE.md; then
    echo "CLAUDE.md is present and valid."
    echo "Test passed."
else
    echo "CLAUDE.md check failed."
    exit 1
fi

cd ..
rm -rf test-next-sqlite
