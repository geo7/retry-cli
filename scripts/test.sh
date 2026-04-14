#!/bin/bash
set -euo pipefail

echo "Running tests (pytest)..."
if [ -n "${CI:-}" ]; then
    # In CI, output a terminal report so it shows up in GitHub Actions logs
    uv run pytest --cov=retry_cli --cov-report=term-missing
else
    # Locally, generate an HTML report for easy viewing
    PYTHONBREAKPOINT=pdbr.set_trace uv run pytest -s -vv --cov=retry_cli --cov-report=html
    echo "Coverage report generated in htmlcov/index.html"
fi
