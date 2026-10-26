@echo off
REM Windows CMD wrapper for claude-review subagent
python "%~dp0agents\pr-reviewer\claude_review.py" %*
