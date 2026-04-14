#!/bin/bash

# e.g:
# bash ./scripts/verify_version.sh v0.1.0

set -euo pipefail

# Allow passing the tag as an argument, otherwise fallback to GITHUB_REF_NAME
TAG_NAME="${1:-${GITHUB_REF_NAME:-}}"

if [ -z "$TAG_NAME" ]; then
    echo "Error: No tag name provided and GITHUB_REF_NAME is not set."
    exit 1
fi

# Remove 'v' prefix if present
TAG_VERSION="${TAG_NAME#v}"

echo "Verifying that tag version '$TAG_VERSION' matches pyproject.toml..."

PACKAGE_VERSION="$(uv run python - <<'PY'
import tomllib
from pathlib import Path
print(tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"])
PY
)"

if [ "$TAG_VERSION" != "$PACKAGE_VERSION" ]; then
    echo "Error: Tag version $TAG_VERSION does not match pyproject.toml version $PACKAGE_VERSION"
    exit 1
fi

echo "Success: Tag version matches package version."
