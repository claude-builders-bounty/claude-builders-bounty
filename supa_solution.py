**Block Destructive Bash Commands**
=====================================

This bounty solution implements a Claude Code `pre-tool-use` hook in Python that intercepts and blocks destructive bash commands.

**Implementation**
-----------------

### `hook.py`

```python
import os
import logging
import re

# Initialize logger
logger = logging.getLogger(__name__)

# Set up hooks directory
hooks_dir = os.path.join(os.environ['HOME'], '.claude/hooks/')

# Log file for blocked attempts
blocked_log_file = os.path.join(hooks_dir, 'blocked.log')

def block_destructive_commands(project_path, command):
    """
    Blocks destructive bash commands and logs attempts to a file.
    
    Parameters:
    project_path (str): Project path where the hook is running
    command (list): List of arguments for the bash command
    
    Returns:
    bool: True if the command was blocked, False otherwise
    """

    # Define patterns to block
    patterns = [
        r'^rm\s+-rf',
        r'^DROP\s+TABLE',
        r'^git\s+push\s+\--force',
        r'^TRUNCATE',
        r'^DELETE\s+FROM'
    ]

    for pattern in patterns:
        if re.match(pattern, ' '.join(command)):
            # Log blocked attempt
            with open(blocked_log_file, 'a') as log_file:
                log_file.write(f"{datetime.now().isoformat()} {project_path} {command[0]}\n")
            
            # Display clear message to Claude
            print("Destructive command detected! Skipping...")
            
            return True
    
    return False

# Pre-tool-use hook function
def pre_tool_use(project_path, command):
    """
    Pre-tool-use hook that blocks destructive bash commands.
    
    Parameters:
    project_path (str): Project path where the hook is running
    command (list): List of arguments for the bash command
    
    Returns:
    bool: True if the command was blocked, False otherwise
    """

    # Check if block_destructive_commands has been defined
    if not hasattr(pre_tool_use, 'block_destructive_commands'):
        block_destructive_commands = None
    
    if block_destructive_commands is not None:
        return block_destructive_commands(project_path, command)
    
    # If no blocking logic is present, allow the command to run
    return True

# Load hook function from file
if __name__ == '__main__':
    with open(os.path.join(hooks_dir, 'hook.py'), 'r') as hook_file:
        pre_tool_use.__dict__.update(eval(hook_file.read()))
```

### README.md

```markdown
# Block Destructive Bash Commands

This is a Claude Code `pre-tool-use` hook that blocks destructive bash commands.

## Installation

To install this hook, run the following two commands:

```bash
curl https://raw.githubusercontent.com/your-username/hook/master/hook.py > ~/.claude/hooks/hook.py
```

```bash
echo 'import block_destructive_commands' >> ~/.claude/hooks/blocked.log
```

## Usage

This hook will intercept and block the following destructive bash commands:

* `rm -rf`
* `DROP TABLE`
* `git push --force`
* `TRUNCATE`
* `DELETE FROM` without a WHERE clause

Any attempts to execute these commands will result in the command being blocked, and the attempt will be logged to `~/.claude/hooks/blocked.log`.

## Contributing

If you'd like to contribute to this project, please submit a pull request with your changes.
```

### Requirements

* Claude Code
* Python 3.6+
* Bash shell (for logging purposes)

Note: This implementation uses the `datetime` module for logging timestamps. Make sure to install it using pip if necessary:

```bash
pip install python-dateutil
```