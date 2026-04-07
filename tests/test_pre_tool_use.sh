# Test for the pre-tool-use hook
# Test if the script blocks the specified destructive commands

# Sample script to simulate command invocation
# Usage: ./test_pre_tool_use.sh "command"

# Function to test blocked command logging
# Arguments: blocked_command
verify_blocked_command() {
    local blocked_command="$1"
    # Invoke the hook with the blocked command
    ~/.claude/hooks/pre-tool-use.sh "$blocked_command"
    # Check the log file for the blocked command
    if grep -q "$blocked_command" ~/.claude/hooks/blocked.log; then
        echo "Test Passed: $blocked_command was successfully blocked."
    else
        echo "Test Failed: $blocked_command was not logged."
    fi
}

# Run tests for each blocked command
verify_blocked_command "rm -rf /"
verify_blocked_command "DROP TABLE users"
verify_blocked_command "git push --force origin master"
verify_blocked_command "TRUNCATE users"
verify_blocked_command "DELETE FROM settings"