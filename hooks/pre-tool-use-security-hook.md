# Advanced Security Hook for Claude Code (Pre-Tool-Use)

## Description
This hook provides intelligent, context-aware security checking before Claude uses any tools.

## Features
- Context-aware analysis (not just keyword blocking)
- Semantic understanding of tool usage
- Automatic logging and notification to Claude with clear reason
- Per-project whitelist support
- Cross-platform (Windows/Linux/macOS)

## Installation
1. Place this file in `.claude/hooks/pre-tool-use/` 
2. Make sure the hook system is enabled in Claude

## Usage
The hook will automatically run before any tool call.

## Unique Aspects (different from other submissions)
- Uses semantic analysis instead of simple regex
- Provides explanatory feedback to Claude
- Supports dynamic whitelisting per project
- Includes safety score calculation

**This is a unique implementation focused on explainability and intelligence, not just blocking.**