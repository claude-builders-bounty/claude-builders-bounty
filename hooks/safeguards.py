#!/usr/bin/env python3
"""
Claude Code pre-tool-use safety hook that blocks destructive commands.
This hook intercepts and blocks potentially destructive commands
to prevent accidental data loss or destructive operations.
"""

import os
import json
import subprocess
import sys
from datetime import datetime

# Dangerous bash operations to block
DANGEROUS_COMMANDS = [
    'rm -rf',
    'DROP TABLE',
    'git push --force',
    'TRUNCATE',
    'DELETE FROM'
]

def check_safety_hooks():
    """Check if the command is in the list of dangerous commands"""
    # Block rm -rf, database drop/truncate, force push and other destructive operations
    return any(command in DANGEROU