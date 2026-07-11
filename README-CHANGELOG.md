# Changelog Generator

This repository contains a bash script to automatically generate a structured CHANGELOG.md from git history.

## Setup

1. Make sure you have git installed on your system
2. Place the `changelog.sh` script in your project root
3. Run with: `bash changelog.sh`

## Features

- Automatically fetches commits since the last git tag
- Categorizes changes into Added, Fixed, Changed, and Removed sections
- Generates properly formatted CHANGELOG.md