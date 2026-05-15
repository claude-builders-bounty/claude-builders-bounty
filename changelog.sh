#!/bin/bash
# Generate CHANGELOG.md from git history — improved version
# Supports: --output, --since, --until, --format, --include-deploy, --verbose, --from-ref
#
# Usage:
#   bash changelog.sh                                     Default CHANGELOG.md
#   bash changelog.sh --output RELEASE.md                 Custom output file
#   bash changelog.sh --since v1.0.0                      Since specific tag
#   bash changelog.sh --until v2.0.0                      Up to specific tag
#   bash changelog.sh --from-ref main..feature             Explicit ref range
#   bash changelog.sh --format json                        JSON output
#   bash changelog.sh --include-deploy                     Add deployment instructions
#   bash changelog.sh --verbose                            Verbose mode

set -euo pipefail

# === Defaults ===
OUTPUT_FILE="CHANGELOG.md"
SINCE=""
UNTIL=""
FROM_REF=""
FORMAT="markdown"
INCLUDE_DEPLOY=false
VERBOSE=false

# Parse flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output|-o)     OUTPUT_FILE="$2"; shift 2 ;;
        --since)         SINCE="$2"; shift 2 ;;
        --until)         UNTIL="$2"; shift 2 ;;
        --from-ref)      FROM_REF="$2"; shift 2 ;;
        --format)        FORMAT="$2"; shift 2 ;;
        --include-deploy) INCLUDE_DEPLOY=true; shift ;;
        --verbose|-v)    VERBOSE=true; shift ;;
        --help|-h)
            echo "Usage: bash changelog.sh [options]"
            echo ""
            echo "Options:"
            echo "  --output, -o FILE     Output file (default: CHANGELOG.md)"
            echo "  --since TAG           Starting ref (e.g., v1.0.0)"
            echo "  --until TAG           Ending ref (e.g., v2.0.0)"
            echo "  --from-ref RANGE      Explicit ref range (e.g., main..feature)"
            echo "  --format FORMAT       Output format: markdown|json (default: markdown)"
            echo "  --include-deploy      Include deployment instructions"
            echo "  --verbose, -v         Show statistics"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Usage: bash changelog.sh [--output FILE] [--since TAG] [--format markdown|json]"
            exit 1
            ;;
    esac
done

# Build git log range
if [ -n "$FROM_REF" ]; then
    RANGE="$FROM_REF"
elif [ -n "$SINCE" ] && [ -n "$UNTIL" ]; then
    RANGE="${SINCE}..${UNTIL}"
elif [ -n "$SINCE" ]; then
    RANGE="${SINCE}..HEAD"
elif [ -n "$UNTIL" ]; then
    FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    RANGE="${FIRST_COMMIT}..${UNTIL}"
else
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    RANGE="${LAST_TAG}..HEAD"
fi

# Get commits
COMMITS=$(git log --format="%H||%s||%an||%ai" "$RANGE" --reverse 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "⚠️  No commits found in range: $RANGE"
    exit 0
fi

# Determine version
if [ -n "$UNTIL" ]; then
    VERSION="$UNTIL"
elif [ -n "$SINCE" ]; then
    VERSION="$SINCE"
else
    VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
fi

DATE=$(date +%Y-%m-%d)

# Deployment template
DEPLOY_TEMPLATE=$(cat <<'DEPLOY_EOF'

## Automated Deployment

This release is ready for automated deployment.

### Deploy Instructions

```bash
# 1. Build the application
npm run build

# 2. Run database migrations
npm run db:migrate

# 3. Deploy to production
# Fly.io:
flyctl deploy --remote-only

# Railway:
# Push to main branch triggers auto-deploy

# 4. Verify deployment
curl -f https://your-app.com/api/health
```

### Environment Variables Required

| Variable | Description | Required |
|----------|-------------|----------|
| `SESSION_SECRET` | JWT signing secret (32+ random bytes) | ✅ |
| `DATABASE_PATH` | Path to SQLite database file | ❌ (default: data/app.db) |
| `NEXT_PUBLIC_APP_URL` | Public URL of the app | ✅ |

### Database Migration Checklist

- [ ] Run migrations on production before deploying new code
- [ ] Back up SQLite file before applying destructive migrations
- [ ] Verify rollback plan for reversible changes

DEPLOY_EOF
)

# Generate Markdown
generate_markdown() {
    local version="$1"
    local date="$2"
    local commits="$3"

    cat <<EOF
# Changelog

All notable changes to this project will be documented in this file.

## [${version}] - ${date}

EOF

    # Categorize and print
    local added="" fixed="" changed="" removed="" docs="" tests="" ci="" security="" perf="" chore=""

    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local msg
        msg=$(echo "$line" | cut -d'|' -f2)
        local hash
        hash=$(echo "$line" | cut -d'|' -f1 | cut -c1-7)
        local clean_msg
        clean_msg=$(echo "$msg" | sed -E 's/^(feat|fix|chore|docs|test|refactor|perf|ci|security)\(?[^)]*\)?: *//i')

        case "$msg" in
            feat:*|add:*|feature:*|new:*)
                added="${added}  - ${clean_msg} (${hash})\n" ;;
            fix:*|bug:*|patch:*|hotfix:*)
                fixed="${fixed}  - ${clean_msg} (${hash})\n" ;;
            change:*|refactor:*|update:*|upgrade:*|improve:*|migrate:*)
                changed="${changed}  - ${clean_msg} (${hash})\n" ;;
            remove:*|delete:*|deprecate:*|drop:*)
                removed="${removed}  - ${clean_msg} (${hash})\n" ;;
            doc:*|docs:*|readme:*)
                docs="${docs}  - ${clean_msg} (${hash})\n" ;;
            test:*|spec:*|coverage:*)
                tests="${tests}  - ${clean_msg} (${hash})\n" ;;
            ci:*|cd:*|deploy:*|pipeline:*)
                ci="${ci}  - ${clean_msg} (${hash})\n" ;;
            security:*|cve:*|vuln:*|auth:*)
                security="${security}  - ${clean_msg} (${hash})\n" ;;
            perf:*|performance:*|optimize:*|speed:*)
                perf="${perf}  - ${clean_msg} (${hash})\n" ;;
            chore:*|bump:*|deps:*|config:*|setup:*)
                chore="${chore}  - ${clean_msg} (${hash})\n" ;;
            *)
                changed="${changed}  - ${clean_msg} (${hash})\n" ;;
        esac
    done <<< "$commits"

    # Print non-empty categories
    [ -n "$added" ]    && echo -e "### Added\n" && echo -en "$added" && echo ""
    [ -n "$fixed" ]    && echo -e "### Fixed\n" && echo -en "$fixed" && echo ""
    [ -n "$changed" ]  && echo -e "### Changed\n" && echo -en "$changed" && echo ""
    [ -n "$removed" ]  && echo -e "### Removed\n" && echo -en "$removed" && echo ""
    [ -n "$security" ] && echo -e "### Security\n" && echo -en "$security" && echo ""
    [ -n "$perf" ]     && echo -e "### Performance\n" && echo -en "$perf" && echo ""
    [ -n "$ci" ]       && echo -e "### CI/CD\n" && echo -en "$ci" && echo ""
    [ -n "$docs" ]     && echo -e "### Documentation\n" && echo -en "$docs" && echo ""
    [ -n "$tests" ]    && echo -e "### Tests\n" && echo -en "$tests" && echo ""
    [ -n "$chore" ]    && echo -e "### Chores\n" && echo -en "$chore" && echo ""

    if [ "$INCLUDE_DEPLOY" = true ]; then
        echo "$DEPLOY_TEMPLATE"
    fi
}

# Generate JSON
generate_json() {
    local version="$1"
    local date="$2"
    local commits="$3"

    # Create temporary files for each category
    local tmp_dir
    tmp_dir=$(mktemp -d)
    local added_file="${tmp_dir}/added.json"
    local fixed_file="${tmp_dir}/fixed.json"
    local changed_file="${tmp_dir}/changed.json"
    local removed_file="${tmp_dir}/removed.json"
    local docs_file="${tmp_dir}/docs.json"
    local tests_file="${tmp_dir}/tests.json"
    local ci_file="${tmp_dir}/ci.json"
    local security_file="${tmp_dir}/security.json"
    local perf_file="${tmp_dir}/perf.json"
    local chore_file="${tmp_dir}/chore.json"

    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local hash msg author date_str
        hash=$(echo "$line" | cut -d'|' -f1 | cut -c1-7)
        msg=$(echo "$line" | cut -d'|' -f2)
        author=$(echo "$line" | cut -d'|' -f3)
        date_str=$(echo "$line" | cut -d'|' -f4)
        local clean_msg
        clean_msg=$(echo "$msg" | sed -E 's/^(feat|fix|chore|docs|test|refactor|perf|ci|security)\(?[^)]*\)?: *//i')
        local entry
        entry=$(cat <<ENTRY
    {"message": "${clean_msg}", "hash": "${hash}", "author": "${author}", "date": "${date_str}"}
ENTRY
)

        case "$msg" in
            feat:*|add:*|feature:*|new:*)             echo "$entry," >> "$added_file" ;;
            fix:*|bug:*|patch:*|hotfix:*)             echo "$entry," >> "$fixed_file" ;;
            change:*|refactor:*|update:*|upgrade:*|improve:*|migrate:*) echo "$entry," >> "$changed_file" ;;
            remove:*|delete:*|deprecate:*|drop:*)     echo "$entry," >> "$removed_file" ;;
            doc:*|docs:*|readme:*)                    echo "$entry," >> "$docs_file" ;;
            test:*|spec:*|coverage:*)                 echo "$entry," >> "$tests_file" ;;
            ci:*|cd:*|deploy:*|pipeline:*)            echo "$entry," >> "$ci_file" ;;
            security:*|cve:*|vuln:*|auth:*)           echo "$entry," >> "$security_file" ;;
            perf:*|performance:*|optimize:*|speed:*)  echo "$entry," >> "$perf_file" ;;
            chore:*|bump:*|deps:*|config:*|setup:*)   echo "$entry," >> "$chore_file" ;;
            *)                                        echo "$entry," >> "$changed_file" ;;
        esac
    done <<< "$commits"

    # Build JSON
    echo "{"
    echo "  \"version\": \"${version}\","
    echo "  \"date\": \"${date}\","
    echo "  \"categories\": {"

    local first_cat=true
    for file in "$added_file" "$fixed_file" "$changed_file" "$removed_file" "$docs_file" "$tests_file" "$ci_file" "$security_file" "$perf_file" "$chore_file"; do
        local name
        name=$(basename "$file" .json)
        if [ -s "$file" ]; then
            # Remove trailing comma from last entry
            local content
            content=$(cat "$file" | sed '$ s/,$//')
            # Capitalize name for display
            local display_name
            case "$name" in
                added) display_name="Added" ;;
                fixed) display_name="Fixed" ;;
                changed) display_name="Changed" ;;
                removed) display_name="Removed" ;;
                docs) display_name="Documentation" ;;
                tests) display_name="Tests" ;;
                ci) display_name="CI/CD" ;;
                security) display_name="Security" ;;
                perf) display_name="Performance" ;;
                chore) display_name="Chores" ;;
            esac
            if [ "$first_cat" = true ]; then
                first_cat=false
            else
                echo ","
            fi
            echo "    \"${display_name}\": ["
            echo "$content"
            echo -n "  ]"
        fi
    done
    echo ""
    echo "  }"

    if [ "$INCLUDE_DEPLOY" = true ]; then
        echo ","
        echo "  \"deployment\": {"
        echo "    \"instructions\": [\"npm run build\", \"npm run db:migrate\", \"flyctl deploy --remote-only\"],"
        echo "    \"env_vars\": {"
        echo "      \"SESSION_SECRET\": \"Required - JWT signing secret\","
        echo "      \"DATABASE_PATH\": \"Optional - default: data/app.db\","
        echo "      \"NEXT_PUBLIC_APP_URL\": \"Required - public URL\""
        echo "    }"
        echo "  }"
    fi
    echo "}"

    rm -rf "$tmp_dir"
}

# Generate output
if [ "$FORMAT" = "json" ]; then
    generate_json "$VERSION" "$DATE" "$COMMITS" > "$OUTPUT_FILE"
else
    generate_markdown "$VERSION" "$DATE" "$COMMITS" > "$OUTPUT_FILE"
fi

echo "✅ CHANGELOG generated to $OUTPUT_FILE"

if [ "$VERBOSE" = true ]; then
    TOTAL=$(echo "$COMMITS" | grep -c '||' || true)
    echo "📊 Statistics:"
    echo "   Output: $OUTPUT_FILE"
    echo "   Format: $FORMAT"
    echo "   Include deploy: $INCLUDE_DEPLOY"
    echo "   Range: $RANGE"
    echo "   Total commits: $TOTAL"
fi
