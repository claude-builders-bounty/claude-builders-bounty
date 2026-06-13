#!/bin/bash



# Claude Code PreToolUse Hook

# Blocks destructive bash commands to prevent accidental damage.



# Read the tool call from stdin

TOOL_CALL=$(cat)



# Extract the command from the tool call JSON

COMMAND=$(echo "$TOOL_CALL" | jq -r '.parameters.command // empty')



if [ -z "$COMMAND" ]; then

  echo "$TOOL_CALL"
  
  exit 0
  
fi



# Define destructive patterns

DESTRUCTIVE_PATTERNS=(

  "rm -rf"
  
  "rm --recursive --force"
  
  "DROP TABLE"
  
  "TRUNCATE"
  
  "git push --force"
  
  "git push -f"
  
)



BLOCKED=false

REASON=""



for PATTERN in "${DESTRUCTIVE_PATTERNS[@]}"; do

  if [[ "$COMMAND" == *"$PATTERN"* ]]; then
  
    BLOCKED=true
    
    REASON="Destructive command pattern detected: $PATTERN"
    
    break
    
  fi
  
done



# Check for DELETE FROM without WHERE

if [[ "$COMMAND" == *"DELETE FROM"* ]] && [[ "$COMMAND" != *"WHERE"* ]]; then

  BLOCKED=true
  
  REASON="DELETE FROM detected without a WHERE clause."
  
fi



if [ "$BLOCKED" = true ]; then

  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  PROJECT_PATH=$(pwd)
  

  
  mkdir -p ~/.claude/hooks
  
  echo "[$TIMESTAMP] BLOCKED: \"$COMMAND\" in $PROJECT_PATH | Reason: $REASON" >> ~/.claude/hooks/blocked.log
  

  
  echo "{\"error\": \"Command blocked by security hook: $REASON. This action is considered destructive and is prohibited for safety reasons.\"}"
  
  exit 1
  
else

  echo "$TOOL_CALL"
  
  exit 0
  
fi
























