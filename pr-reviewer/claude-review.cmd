@echo off
REM Windows wrapper so claude-review --pr ^<url^> works without installing.
node "%~dp0bin\claude-review.mjs" %*
