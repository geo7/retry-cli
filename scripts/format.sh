#!/bin/bash
set -euo pipefail

if [ -n "${CI:-}" ]; then
    FORMAT_RETRY_COUNT=0
    FIX_RETRY_COUNT=0
else
    FORMAT_RETRY_COUNT=2
    FIX_RETRY_COUNT=2
fi

echo "Formatting code with ruff format/check..."
uv run retry --retries "${FORMAT_RETRY_COUNT}" --command "uv run ruff format ."
uv run retry --retries "${FIX_RETRY_COUNT}" --command "uv run ruff check . --fix-only --unsafe-fixes"
echo "(finished formatting)"
