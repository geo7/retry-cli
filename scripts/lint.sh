#!/bin/bash
set -euo pipefail

if [ -n "${CI:-}" ]; then
    FORMAT_RETRY_COUNT=0
    LINT_RETRY_COUNT=0
else
    FORMAT_RETRY_COUNT=2
    LINT_RETRY_COUNT=2
fi

echo "Checking ruff formatting..."
uv run retry --retries "${FORMAT_RETRY_COUNT}" --command "uv run ruff format . --check"

echo "Linting with ruff..."
uv run retry --retries "${LINT_RETRY_COUNT}" --command "uv run ruff check ."
