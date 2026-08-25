@echo off
rem claude-review — Windows shim: `claude-review.cmd --pr https://...`
python "%~dp0claude_review.py" %*
