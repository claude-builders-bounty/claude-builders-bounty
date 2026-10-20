#!/usr/bin/env bash
exec python3 "$(dirname -- "$0")/changelog.py" "$@"
