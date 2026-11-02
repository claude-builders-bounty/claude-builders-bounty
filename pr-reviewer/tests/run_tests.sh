#!/bin/sh
set -e
cd "$(dirname "$0")/../.."
exec python3 -m unittest discover -s pr-reviewer/tests -v
