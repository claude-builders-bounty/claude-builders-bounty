#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.
"""

import os
import re
import sys
import time
from pathlib import Path

def log_blocked_command(command, project_path):
    """Log blocked command attempts with timestamp and project path."""
    log_file = Path.home() / ".cla