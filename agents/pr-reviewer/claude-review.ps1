$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\claude_review.py" @args
