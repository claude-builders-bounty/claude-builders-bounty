# Test blocking rm -rf
echo "rm -rf /tmp/test" | ~/.claude/hooks/pre-tool-use
# Should output: Error: Command blocked...

# Test allowing safe commands
echo "ls -la" | ~/.claude/hooks/pre-tool-use
# Should output: ls -la

# Check the log
cat ~/.claude/hooks/blocked.log
# Should show the blocked attempt with timestamp