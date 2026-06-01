@echo off
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%..\agents\pr-reviewer\claude_review.py" %*
