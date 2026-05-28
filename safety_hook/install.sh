#!/bin/bash
chmod +x "$(dirname "${BASH_SOURCE[0]}")/claude_guardian.py"
echo "Claude Guardian ready. Use: python3 safety_hook/claude_guardian.py \"<command>\""
