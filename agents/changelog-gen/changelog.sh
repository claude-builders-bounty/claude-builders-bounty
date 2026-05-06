#!/bin/bash

# changelog.sh - Automatically generate a structured CHANGELOG.md from git history
# Categories: Added, Fixed, Changed, Removed

# Ensure we are in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "Error: Not a git repository."
    exit 1
    fi

    # Get the last tag, or the first commit if no tags exist
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

    if [ -z "$LAST_TAG" ]; then
      echo "No tags found. Generating changelog from initial commit..."
        RANGE="HEAD"
        else
          echo "Generating changelog since tag: $LAST_TAG"
            RANGE="$LAST_TAG..HEAD"
            fi

            # Temporary files for categories
            TMP_ADDED=$(mktemp)
            TMP_FIXED=$(mktemp)
            TMP_CHANGED=$(mktemp)
            TMP_REMOVED=$(mktemp)
            TMP_OTHER=$(mktemp)

            # Fetch commits and categorize
            git log "$RANGE" --pretty=format:"%s" | while read -r message; do
              if [[ "$message" =~ ^(feat|add|Added) ]]; then
                  echo "- $message" >> "$TMP_ADDED"
                    elif [[ "$message" =~ ^(fix|Fixed) ]]; then
                        echo "- $message" >> "$TMP_FIXED"
                          elif [[ "$message" =~ ^(refactor|change|Changed) ]]; then
                              echo "- $message" >> "$TMP_CHANGED"
                                elif [[ "$message" =~ ^(remove|Removed|delete) ]]; then
                                    echo "- $message" >> "$TMP_REMOVED"
                                      else
                                          echo "- $message" >> "$TMP_OTHER"
                                            fi
                                            done

                                            # Build CHANGELOG.md
                                            VERSION_DATE=$(date +%Y-%m-%d)
                                            NEW_CHANGELOG=$(mktemp)

                                            echo "# CHANGELOG" > "$NEW_CHANGELOG"
                                            echo "" >> "$NEW_CHANGELOG"
                                            echo "## [$VERSION_DATE]" >> "$NEW_CHANGELOG"
                                            echo "" >> "$NEW_CHANGELOG"

                                            write_section() {
                                              local title="$1"
                                                local file="$2"
                                                  if [ -s "$file" ]; then
                                                      echo "### $title" >> "$NEW_CHANGELOG"
                                                          cat "$file" >> "$NEW_CHANGELOG"
                                                              echo "" >> "$NEW_CHANGELOG"
                                                                fi
                                                                }

                                                                write_section "Added" "$TMP_ADDED"
                                                                write_section "Fixed" "$TMP_FIXED"
                                                                write_section "Changed" "$TMP_CHANGED"
                                                                write_section "Removed" "$TMP_REMOVED"
                                                                write_section "Other" "$TMP_OTHER"

                                                                # Append existing changelog if it exists
                                                                if [ -f CHANGELOG.md ]; then
                                                                  grep -v "^# CHANGELOG" CHANGELOG.md >> "$NEW_CHANGELOG"
                                                                  fi

                                                                  mv "$NEW_CHANGELOG" CHANGELOG.md

                                                                  # Cleanup
                                                                  rm "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"

                                                                  echo "CHANGELOG.md updated successfully."
                                                                  
