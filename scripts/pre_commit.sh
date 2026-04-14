#!/bin/bash
set -euo pipefail

if [ -n "${CI:-}" ]; then
    PRE_COMMIT_RETRY_COUNT=0
else
    PRE_COMMIT_RETRY_COUNT=2
fi

echo "Running pre-commit on all files..."
uv run retry --retries "${PRE_COMMIT_RETRY_COUNT}" --command "pre-commit run --all-files"
