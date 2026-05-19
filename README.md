# AI Changelog Generator

A simple Python tool that extracts git commit history and uses **Google Gemini 1.5 Flash** to automatically generate a structured, professional `CHANGELOG.md`.

## Features
- Fetches git commit logs locally.
- Uses Gemini AI for intelligent grouping (Features, Bug Fixes, Documentation).
- Blazing fast and cost-effective generation.
- CLI arguments for timeframe scoping (e.g. `1 month ago`, `<tagname>..HEAD`).

## Requirements
- Python 3.8+
- `google-generativeai` library

## Installation
```bash
pip install google-generativeai
```

## Usage

1. Set your Gemini API Key:
```bash
export GEMINI_API_KEY="your-api-key"
```

2. Run the generator in your git repository:
```bash
python generate_changelog.py --since="1 week ago"
```

### Options
- `--since`: Git timeframe argument. Defaults to `1 month ago`. Can be anything `git log --since` accepts.
- `--output`: Name of the file to save the markdown output. Defaults to `CHANGELOG.md`.
