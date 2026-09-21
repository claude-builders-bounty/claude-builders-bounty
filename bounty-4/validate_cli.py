from pathlib import Path
import re
root=Path(__file__).parent
text=(root/'.claude/agents/pr-reviewer.md').read_text()
for h in ['## Summary','## Identified risks','## Improvement suggestions','## Confidence']:
    assert h in text
cli=(root/'bin/claude-review').read_text()
assert '--pr' in cli and '--diff-file' in cli and "'--agent','pr-reviewer'" in cli
print('ok')
